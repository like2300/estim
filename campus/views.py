import uuid
import requests
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (Annonce, Cours, CampusApp, Notification, Etablissement, 
                     Niveau, Filiere, HeroImage, Resultat, Examen, SessionExamen, Transaction)
from .serializers import (AnnonceSerializer, CoursSerializer, CampusAppSerializer,
                                NotificationSerializer, EtablissementSerializer,
                                NiveauSerializer, FiliereSerializer, HeroImageSerializer, 
                                ResultatSerializer, ExamenSerializer, SessionExamenSerializer, TransactionSerializer)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=False, methods=['post'])
    def create_pay_link(self, request):
        payer_matricule = request.data.get('payer_matricule')
        target_matricule = request.data.get('target_matricule')
        session_id = request.data.get('session_id')
        
        if not all([payer_matricule, target_matricule, session_id]):
            return Response({"error": "Données manquantes"}, status=400)

        # Vérifier si l'étudiant cible existe réellement dans cette session
        if not Resultat.objects.filter(matricule=target_matricule, session_id=session_id).exists():
            return Response({"error": "Impossible de payer : cet étudiant n'existe pas dans cette session"}, status=404)

        # Vérifier si déjà payé
        if Transaction.objects.filter(
            payer_matricule=payer_matricule, 
            target_matricule=target_matricule, 
            session_id=session_id, 
            status="SUCCESS"
        ).exists():
            return Response({"message": "Déjà payé", "already_paid": True})

        transaction_ref = str(uuid.uuid4())
        amount = 100 # XAF
        
        # Récupérer le nom de l'étudiant payeur pour pré-remplir le lien OpenPay
        payer_name = "Étudiant"
        etudiant = Resultat.objects.filter(matricule=payer_matricule).first()
        if etudiant:
            payer_name = etudiant.nom_etudiant

        # Payload selon la documentation "Créer un lien de paiement"
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
        
        try:
            # URL exacte de la doc: https://api.openpay-cg.com/v1/payment-link
            response = requests.post(
                "https://api.openpay-cg.com/v1/payment-link", 
                json=payload, 
                headers=headers
            )
            
            try:
                data = response.json()
            except:
                data = {"raw_response": response.text}
            
            if response.status_code in [200, 201]:
                res_data = data.get("data", {})
                # Important: use OPENPAY's reference if returned, otherwise our UUID
                openpay_ref = res_data.get("reference") or transaction_ref
                
                Transaction.objects.create(
                    payer_matricule=payer_matricule,
                    target_matricule=target_matricule,
                    session_id=session_id,
                    amount=amount,
                    transaction_ref=openpay_ref,
                    status="PENDING"
                )
                return Response({
                    "payment_url": res_data.get("payment_url", ""), 
                    "transaction_ref": openpay_ref
                })
            else:
                print(f"DEBUG OPENPAY ERROR {response.status_code}: {data}")
                return Response({"error": "Erreur OpenPay", "details": data}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='webhook')
    def webhook(self, request):
        # Log the incoming payload for debugging
        print(f"DEBUG: Webhook received payload: {request.data}")
        
        # Certains processeurs enveloppent les données dans 'data'
        payload = request.data.get('data', request.data)
        
        # OpenPay uses 'reference' or 'transaction_ref'
        metadata = payload.get('metadata') or {}
        # Try to find reference in various possible fields
        ref = (
            metadata.get('transaction_ref') or 
            payload.get('reference') or 
            payload.get('transaction_ref') or 
            payload.get('payment_token')
        )
        
        status_val = str(payload.get('status', '')).upper() # success, SUCCESS, PAID, COMPLETED...
        
        if not ref:
            print("ERROR: Missing reference in webhook payload")
            return Response({"error": "Référence manquante"}, status=400)
        
        try:
            # Try to find transaction by reference
            trans = Transaction.objects.filter(transaction_ref=ref).first()
            
            if not trans:
                print(f"ERROR: Transaction with ref {ref} not found")
                return Response({"error": "Transaction non trouvée"}, status=404)

            if status_val in ["SUCCESS", "SUCCESSFUL", "PAID", "COMPLETED"]:
                trans.status = "SUCCESS"
            elif status_val in ["FAILED", "EXPIRED", "CANCELLED", "ERROR"]:
                trans.status = "FAILED"
            
            trans.save()
            print(f"INFO: Transaction {ref} updated to {trans.status}")
            return Response({"status": "ok", "message": f"Transaction {ref} mise à jour : {trans.status}"})
        except Exception as e:
            print(f"CRITICAL: Webhook error: {str(e)}")
            return Response({"error": str(e)}, status=500)

class SessionExamenViewSet(viewsets.ModelViewSet):
    queryset = SessionExamen.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = SessionExamenSerializer

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
            queryset = queryset.filter(matricule=matricule)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
            
        return queryset

    @action(detail=False, methods=['get'])
    def consulter(self, request):
        matricule = request.query_params.get('matricule')
        session_id = request.query_params.get('session')
        payer_matricule = request.query_params.get('payer_matricule')

        if not matricule or not session_id:
            return Response({"error": "Matricule et session sont requis"}, status=400)

        # 1. Vérifier si la session existe
        try:
            session = SessionExamen.objects.get(id=session_id)
        except SessionExamen.DoesNotExist:
            return Response({"error": "Session non trouvée"}, status=404)

        # 2. Vérifier si les résultats existent pour ce matricule dans cette session
        # AVANT de demander un paiement
        if not Resultat.objects.filter(matricule=matricule, session=session).exists():
            return Response({"error": "Aucun résultat trouvé pour ce matricule dans cette session"}, status=404)

        # 3. Vérification si c'est son propre résultat ou si payé
        if matricule != payer_matricule:
            # Vérifier si une transaction SUCCESS existe
            paid = Transaction.objects.filter(
                payer_matricule=payer_matricule, 
                target_matricule=matricule, 
                session_id=session_id, 
                status="SUCCESS"
            ).exists()
            
            if not paid:
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
