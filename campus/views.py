import uuid
import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (Annonce, Cours, CampusApp, Notification, Etablissement, 
                     Niveau, Filiere, HeroImage, Resultat, Examen, SessionExamen, Transaction, Paiement)
from .serializers import (AnnonceSerializer, CoursSerializer, CampusAppSerializer,
                                NotificationSerializer, EtablissementSerializer,
                                NiveauSerializer, FiliereSerializer, HeroImageSerializer, 
                                ResultatSerializer, ExamenSerializer, SessionExamenSerializer, 
                                TransactionSerializer, PaiementSerializer)

def verify_openpay_status(trans):
    """Fonction utilitaire pour vérifier et mettre à jour le statut d'une transaction"""
    headers = {
        "XO-API-KEY": settings.OPENPAY_API_KEY,
        "Accept": "application/json"
    }
    try:
        response = requests.get(
            f"https://api.openpay-cg.com/v1/payment-link/{trans.transaction_ref}", 
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json().get("data", {})
            status_val = str(data.get("status", "")).upper()
            
            success_statuses = ["SUCCESS", "SUCCESSFUL", "PAID", "COMPLETED", "APPROVED", "COMPLÉTÉ"]
            fail_statuses = ["FAILED", "EXPIRED", "CANCELLED", "ERROR", "DECLINED", "ÉCHOUÉ"]
            
            if status_val in success_statuses:
                trans.status = "SUCCESS"
                trans.save()
                Paiement.objects.get_or_create(
                    reference=trans.transaction_ref,
                    defaults={
                        'payer_matricule': trans.payer_matricule,
                        'target_matricule': trans.target_matricule,
                        'session': trans.session,
                        'amount': trans.amount,
                        'payment_method': data.get('payment_method', 'OpenPay')
                    }
                )
                return True
            elif status_val in fail_statuses:
                trans.status = "FAILED"
                trans.save()
        return False
    except Exception as e:
        print(f"ERROR in verify_openpay_status: {str(e)}")
        return False

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_field = 'transaction_ref'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Si la transaction est toujours en attente, on tente une vérification proactive
        if instance.status == "PENDING":
            print(f"DEBUG: Proactive check for transaction {instance.transaction_ref}")
            verify_openpay_status(instance)
            # Re-fetch from DB
            instance.refresh_from_db()
            
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def create_pay_link(self, request):
        target_matricule = str(request.data.get('target_matricule', '')).strip().upper()
        session_id = request.data.get('session_id')
        payer_matricule = str(request.data.get('payer_matricule', '')).strip().upper()
        
        if not target_matricule or not session_id or not payer_matricule:
            return Response({"error": "Matricule cible, matricule payeur et ID de session sont requis"}, status=400)

        # Vérifier si la session existe et si les résultats sont disponibles
        try:
            session = SessionExamen.objects.get(id=session_id)
            if not session.results_available:
                return Response({
                    "error": "Les résultats de cette session ne sont pas encore ouverts à la consultation.",
                    "available": False
                }, status=400)
        except SessionExamen.DoesNotExist:
            return Response({"error": "Session non trouvée"}, status=404)

        # Bloquer si on essaie de payer pour son propre matricule (ça doit être gratuit)
        if target_matricule == payer_matricule:
            return Response({
                "error": "Vous ne pouvez pas payer pour votre propre matricule. Veuillez le configurer dans votre profil pour y accéder gratuitement.",
                "is_self_payment": True
            }, status=400)

        # Vérifier si l'étudiant cible existe réellement dans cette session
        if not Resultat.objects.filter(matricule=target_matricule, session=session).exists():
            return Response({"error": f"L'étudiant avec le matricule {target_matricule} n'existe pas dans cette session"}, status=404)

        # Vérifier si déjà payé
        if Paiement.objects.filter(
            payer_matricule=payer_matricule, 
            target_matricule=target_matricule, 
            session=session
        ).exists():
            return Response({"message": "Déjà payé", "already_paid": True})

        transaction_ref = str(uuid.uuid4())
        amount = 100 # XAF
        
        # Récupérer le nom de l'étudiant payeur pour pré-remplir le lien OpenPay
        payer_name = "Étudiant"
        if payer_matricule.startswith("ANONYMOUS") or payer_matricule == "INVITE":
            # Extraire une partie de l'ID pour le nom (ex: ANONYMOUS_123456 -> Visiteur 123456)
            suffix = payer_matricule.split('_')[-1] if '_' in payer_matricule else "Visiteur"
            payer_name = f"Visiteur {suffix}"
        else:
            etudiant = Resultat.objects.filter(matricule=payer_matricule).first()
            if etudiant:
                payer_name = etudiant.nom_etudiant

        # Payload selon la documentation OpenPay CG
        payload = {
            "amount": amount,
            "description": f"Consultation résultat {target_matricule}",
            "success_url": "https://estim-campus.com/payment-success",
            "customer": {
                "name": payer_name
            },
            "metadata": {
                "transaction_ref": transaction_ref,
                "payer": payer_matricule,
                "target": target_matricule,
                "session": session_id
            }
        }
        
        headers = {
            "XO-API-KEY": settings.OPENPAY_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"DEBUG: Sending to OpenPay: {payload}")
        
        try:
            response = requests.post(
                "https://api.openpay-cg.com/v1/payment-link", 
                json=payload, 
                headers=headers
            )
            
            try:
                data = response.json()
            except:
                data = {"raw_response": response.text}
            
            print(f"DEBUG: OpenPay response {response.status_code}: {data}")
            
            if response.status_code in [200, 201]:
                res_data = data.get("data", {})
                # Important: use payment_token or reference if returned
                openpay_ref = res_data.get("payment_token") or res_data.get("reference") or transaction_ref
                
                Transaction.objects.create(
                    payer_matricule=payer_matricule,
                    target_matricule=target_matricule,
                    session=session,
                    amount=amount,
                    transaction_ref=openpay_ref,
                    status="PENDING"
                )
                return Response({
                    "payment_url": res_data.get("payment_url", ""), 
                    "transaction_ref": openpay_ref
                })
            else:
                return Response({"error": "Erreur lors de la communication avec OpenPay", "details": data}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            print(f"CRITICAL ERROR calling OpenPay: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='confirm/(?P<ref>[^/.]+)')
    def confirm_payment(self, request, ref=None):
        """
        Action manuelle pour vérifier le statut d'une transaction auprès d'OpenPay
        au cas où le webhook n'aurait pas encore été reçu.
        """
        if not ref:
            return Response({"error": "Référence manquante"}, status=400)
            
        trans = Transaction.objects.filter(transaction_ref=ref).first()
        if not trans:
            return Response({"error": "Transaction non trouvée"}, status=404)
            
        if trans.status == "SUCCESS":
            return Response({"status": "SUCCESS", "message": "Déjà confirmé"})
            
        success = verify_openpay_status(trans)
        
        if success:
            return Response({"status": "SUCCESS", "message": "Paiement confirmé avec succès"})
        
        # Refresh to see if status changed to FAILED or stayed PENDING
        trans.refresh_from_db()
        if trans.status == "FAILED":
            return Response({"status": "FAILED", "message": "Le paiement a échoué ou a été annulé"})
            
        return Response({"status": "PENDING", "message": "Le paiement est toujours en attente"})

    @action(detail=False, methods=['post'], url_path='webhook')
    def webhook(self, request):
        # Log the incoming payload for debugging
        print(f"--- WEBHOOK RECEIVED ---")
        print(f"Headers: {request.headers}")
        print(f"Data: {request.data}")
        
        # Certains processeurs enveloppent les données dans 'data'
        payload = request.data.get('data', request.data)
        metadata = payload.get('metadata') or {}
        
        # Liste exhaustive des champs possibles pour la référence
        possible_refs = [
            payload.get('payment_token'),
            payload.get('reference'),
            payload.get('transaction_ref'),
            metadata.get('transaction_ref'),
            payload.get('payment_id'),
            request.data.get('payment_token'),
            request.data.get('reference')
        ]
        
        # Filtrer les refs non nulles
        valid_refs = [str(r) for r in possible_refs if r]
        
        print(f"DEBUG: Potential references: {valid_refs}")
        
        if not valid_refs:
            print("ERROR: Missing reference in webhook payload")
            return Response({"error": "Référence manquante"}, status=400)
        
        # Status detection
        # On regarde dans status, mais aussi payment_status qui est courant
        status_val = str(payload.get('status') or payload.get('payment_status') or '').upper()
        if not status_val:
            # Essayer de voir si c'est un succès direct via un booléen
            if payload.get('success') is True or payload.get('paid') is True:
                status_val = "SUCCESS"
        
        print(f"DEBUG: Detected STATUS={status_val}")
        
        try:
            # Try to find transaction using ANY of the references found
            trans = Transaction.objects.filter(transaction_ref__in=valid_refs).first()
            
            if not trans:
                print(f"ERROR: No transaction found for any of the refs: {valid_refs}")
                return Response({"error": "Transaction non trouvée"}, status=200)

            success_statuses = ["SUCCESS", "SUCCESSFUL", "PAID", "COMPLETED", "APPROVED", "COMPLÉTÉ"]
            fail_statuses = ["FAILED", "EXPIRED", "CANCELLED", "ERROR", "DECLINED", "ÉCHOUÉ"]

            if status_val in success_statuses:
                trans.status = "SUCCESS"
                # Créer un enregistrement dans Paiement
                Paiement.objects.get_or_create(
                    reference=trans.transaction_ref,
                    defaults={
                        'payer_matricule': trans.payer_matricule,
                        'target_matricule': trans.target_matricule,
                        'session': trans.session,
                        'amount': trans.amount,
                        'payment_method': payload.get('payment_method', 'OpenPay')
                    }
                )
                print(f"SUCCESS: Paiement recorded for {trans.target_matricule}")
            elif status_val in fail_statuses:
                trans.status = "FAILED"
            
            trans.save()
            print(f"SUCCESS: Transaction updated to {trans.status}")
            return Response({"status": "ok"})
        except Exception as e:
            print(f"CRITICAL: Webhook error: {str(e)}")
            return Response({"error": str(e)}, status=500)

class SessionExamenViewSet(viewsets.ModelViewSet):
    queryset = SessionExamen.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = SessionExamenSerializer

class PaiementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paiement.objects.all().order_by('-created_at')
    serializer_class = PaiementSerializer

    def get_queryset(self):
        queryset = Paiement.objects.all()
        payer = self.request.query_params.get('payer_matricule')
        if payer:
            queryset = queryset.filter(payer_matricule=str(payer).strip().upper())
        return queryset.order_by('-created_at')

class AnnonceViewSet(viewsets.ModelViewSet):
    queryset = Annonce.objects.all().order_by('-date')
    serializer_class = AnnonceSerializer

class EtablissementViewSet(viewsets.ModelViewSet):
    queryset = Etablissement.objects.all()
    serializer_class = EtablissementSerializer

class NiveauViewSet(viewsets.ModelViewSet):
    queryset = Niveau.objects.all()
    serializer_class = NiveauSerializer

class FiliereViewSet(viewsets.ModelViewSet):
    queryset = Filiere.objects.all()
    serializer_class = FiliereSerializer

class ResultatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Resultat.objects.all()
    serializer_class = ResultatSerializer

    def get_queryset(self):
        queryset = Resultat.objects.all()
        matricule = self.request.query_params.get('matricule')
        session_id = self.request.query_params.get('session')

        if matricule:
            queryset = queryset.filter(matricule=str(matricule).strip().upper())
        if session_id:
            queryset = queryset.filter(session_id=session_id)
            
        return queryset

    @action(detail=False, methods=['get'])
    def consulter(self, request):
        matricule = str(request.query_params.get('matricule', '')).strip().upper()
        session_id = request.query_params.get('session')
        payer_matricule = str(request.query_params.get('payer_matricule', '')).strip().upper()
        anonymous_id = str(request.query_params.get('anonymous_id', '')).strip().upper()

        if not matricule or not session_id:
            return Response({"error": "Matricule et session sont requis"}, status=400)

        # 1. Vérifier si la session existe
        try:
            session = SessionExamen.objects.get(id=session_id)
        except SessionExamen.DoesNotExist:
            return Response({"error": "Session non trouvée"}, status=404)

        # 2. Vérifier si les résultats existent pour ce matricule dans cette session
        if not Resultat.objects.filter(matricule=matricule, session=session).exists():
            return Response({"error": f"Aucun résultat trouvé pour le matricule {matricule} dans cette session"}, status=404)

        # 3. Vérification si c'est son propre résultat ou si payé
        # On considère comme payé si:
        # a) matricule == payer_matricule (consultation propre)
        # b) Un enregistrement Paiement existe pour (payer_matricule, target_matricule)
        # c) Un enregistrement Paiement existe pour (anonymous_id, target_matricule)
        
        is_own_result = (payer_matricule == matricule)
        
        # Filtre de base pour le paiement
        payment_query = Q(target_matricule=matricule, session=session)
        
        # On construit les conditions de "qui a pu payer"
        # On inclut toujours le matricule cible au cas où il aurait payé pour lui-même (même si bloqué par l'UI)
        payer_conditions = Q(payer_matricule=matricule) 
        
        if payer_matricule and payer_matricule != "NONE" and payer_matricule != "NULL":
            payer_conditions |= Q(payer_matricule=payer_matricule)
        if anonymous_id and anonymous_id != "NONE" and anonymous_id != "NULL":
            payer_conditions |= Q(payer_matricule=anonymous_id)
            
        paid = Paiement.objects.filter(payment_query & payer_conditions).exists()

        # Si pas encore marqué comme payé, on vérifie si une transaction PENDING existe et on tente de la confirmer
        if not is_own_result and not paid:
            pending_trans = Transaction.objects.filter(
                target_matricule=matricule,
                session=session,
                status="PENDING"
            ).filter(payer_conditions).first()
            
            if pending_trans:
                print(f"DEBUG: Found PENDING transaction during consultation for {matricule}. Verifying...")
                if verify_openpay_status(pending_trans):
                    paid = True
                    print(f"DEBUG: Proactive verification successful for {matricule}")

        if not is_own_result and not paid:
             return Response({
                "requires_payment": True,
                "amount": 100,
                "message": "La consultation du résultat d'un autre étudiant nécessite un paiement de 100 XAF."
            }, status=200)

        # 4. Vérifier si les résultats sont disponibles (ouverts par l'admin)
        if not session.results_available:
            return Response({
                "available": False,
                "message": "Les résultats ne sont pas encore disponibles. Veuillez contacter le service client ou votre établissement."
            }, status=200)

        # 5. Renvoyer le résultat
        try:
            resultat = Resultat.objects.get(matricule=matricule, session=session)
            serializer = self.get_serializer(resultat)
            return Response({
                "available": True,
                "data": serializer.data
            })
        except Resultat.DoesNotExist:
            return Response({"error": "Résultat non trouvé"}, status=404)

class HeroImageViewSet(viewsets.ModelViewSet):
    queryset = HeroImage.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = HeroImageSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    serializer_class = NotificationSerializer

class CoursViewSet(viewsets.ModelViewSet):
    queryset = Cours.objects.all()
    serializer_class = CoursSerializer

    def get_queryset(self):
        queryset = Cours.objects.all()
        day = self.request.query_params.get('day')
        etablissement = self.request.query_params.get('etablissement')
        niveau = self.request.query_params.get('niveau')
        filiere = self.request.query_params.get('filiere')

        if day:
            queryset = queryset.filter(day_of_week=day)
        if etablissement and etablissement != 'Tous':
            queryset = queryset.filter(etablissement__nom=etablissement)
        if niveau and niveau != 'Tous':
            queryset = queryset.filter(niveau__nom=niveau)
        if filiere and filiere != 'Toutes':
            queryset = queryset.filter(filiere__nom=filiere)
            
        return queryset

class CampusAppViewSet(viewsets.ModelViewSet):
    queryset = CampusApp.objects.all()
    serializer_class = CampusAppSerializer

class ExamenViewSet(viewsets.ModelViewSet):
    queryset = Examen.objects.all()
    serializer_class = ExamenSerializer

    def get_queryset(self):
        queryset = Examen.objects.all()
        etablissement = self.request.query_params.get('etablissement')
        niveau = self.request.query_params.get('niveau')
        filiere = self.request.query_params.get('filiere')

        if etablissement and etablissement != 'Tous':
            queryset = queryset.filter(etablissement__nom=etablissement)
        if niveau and niveau != 'Tous':
            queryset = queryset.filter(niveau__nom=niveau)
        if filiere and filiere != 'Toutes':
            queryset = queryset.filter(filiere__nom=filiere)
            
        return queryset.order_by('date', 'heure')
