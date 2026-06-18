import io
import os
import ssl
import urllib.parse
import urllib.request

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import Image as RLImage
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from django.db.models import Q
from .models import FormConfig, Inscription
from .serializers import InscriptionSerializer, FormConfigSerializer

class FormConfigViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FormConfig.objects.all()
    serializer_class = FormConfigSerializer

    @action(detail=False, methods=['get'])
    def current(self, request):
        config = self.queryset.filter(is_active=True).first()
        if not config:
            return Response({"error": "No active config"}, status=404)
        serializer = self.get_serializer(config)
        return Response(serializer.data)

def verify_inscription(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk)
    from django.utils import timezone

    return render(
        request,
        "inscription/verify.html",
        {"inscription": inscription, "now": timezone.now()},
    )


class InscriptionViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def perform_create(self, serializer):
        config = FormConfig.objects.filter(is_active=True).first()
        annee = config.annee_academique if config else "2025-2026"
        serializer.save(annee_academique=annee)

    @action(detail=False, methods=['get'])
    def consulter(self, request):
        pk = request.query_params.get('pk')
        payer_matricule = str(request.query_params.get('payer_matricule', '')).strip().upper()
        anonymous_id = str(request.query_params.get('anonymous_id', '')).strip().upper()

        if not pk:
            return Response({"error": "ID d'inscription est requis", "available": False}, status=400)

        try:
            inscription = Inscription.objects.get(pk=pk)
        except Inscription.DoesNotExist:
            return Response({
                "available": False, 
                "error": f"Inscription avec l'ID #{pk} introuvable dans la base de données."
            }, status=200)
        except Exception as e:
            return Response({
                "available": False, 
                "error": f"Erreur système lors de la recherche : {str(e)}"
            }, status=500)

        serializer = self.get_serializer(inscription)
        return Response({
            "available": True,
            "data": serializer.data
        })

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        inscription = get_object_or_404(Inscription, pk=pk)

        is_admin = request.query_params.get("admin") == "1"
        if is_admin and not (request.user and request.user.is_staff):
            return Response({"detail": "Accès administratif non autorisé."}, status=status.HTTP_403_FORBIDDEN)

        buffer = io.BytesIO()
        page_w, page_h = A4
        usable_w = page_w - 56

        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=20, bottomMargin=18)

        C_GREEN = colors.HexColor("#1a6b3c")
        C_GREEN_DARK = colors.HexColor("#145530")
        C_GREEN_LIGHT = colors.HexColor("#e8f5e9")
        C_GOLD = colors.HexColor("#c8960a")
        C_DARK = colors.HexColor("#1a2332")
        C_GRAY_DARK = colors.HexColor("#555555")
        C_GRAY = colors.HexColor("#777777")
        C_GRAY_LIGHT = colors.HexColor("#999999")
        C_GRAY_PALE = colors.HexColor("#d0d7de")
        C_ROW_ALT = colors.HexColor("#f6f9f6")
        C_WHITE = colors.white
        C_ADMIN = colors.HexColor("#c62828")

        s_title_header = ParagraphStyle("sTitleH", fontSize=12.5, leading=15, fontName="Helvetica-Bold", textColor=C_GREEN, alignment=TA_CENTER)
        s_agrement = ParagraphStyle("sAgrement", fontSize=7.5, leading=9.5, fontName="Helvetica-BoldOblique", textColor=C_GRAY_DARK, alignment=TA_CENTER)
        s_address_header = ParagraphStyle("sAddrH", fontSize=6.5, leading=8.5, fontName="Helvetica", textColor=C_GRAY, alignment=TA_CENTER)
        s_subtitle = ParagraphStyle("sSub", fontSize=10.5, leading=13, fontName="Helvetica-Bold", textColor=C_GOLD, alignment=TA_CENTER)
        s_etab = ParagraphStyle("sEtab", fontSize=9, leading=12, fontName="Helvetica-Bold", textColor=C_DARK, alignment=TA_LEFT)
        s_section = ParagraphStyle("sSec", fontSize=8, leading=10, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_LEFT)
        s_label = ParagraphStyle("sLabel", fontSize=7, leading=9.5, fontName="Helvetica-Bold", textColor=C_GREEN, alignment=TA_LEFT)
        s_value_mono = ParagraphStyle("sValM", fontSize=7.5, leading=9.5, fontName="Courier", textColor=C_DARK, alignment=TA_LEFT)
        s_sig_label = ParagraphStyle("sSig", fontSize=6.5, leading=8, fontName="Helvetica", textColor=C_GRAY, alignment=TA_CENTER)
        s_sig_name = ParagraphStyle("sSigN", fontSize=7.5, leading=9, fontName="Helvetica-Bold", textColor=C_DARK, alignment=TA_CENTER)
        s_ref = ParagraphStyle("sRef", fontSize=6, leading=7.5, fontName="Helvetica", textColor=C_GRAY_LIGHT, alignment=TA_RIGHT)
        s_qr_text = ParagraphStyle("QRText", fontSize=5.5, leading=7.5, textColor=C_GRAY, alignment=TA_LEFT)
        s_admin_badge = ParagraphStyle("sAdmBadge", fontSize=6, leading=7, fontName="Helvetica-Bold", textColor=C_WHITE, alignment=TA_CENTER)
        s_admin_label = ParagraphStyle("sAdmLbl", fontSize=6, leading=7.5, fontName="Helvetica-Bold", textColor=C_ADMIN, alignment=TA_LEFT)
        s_admin_value = ParagraphStyle("sAdmVal", fontSize=6.5, leading=8, fontName="Helvetica", textColor=C_GRAY_DARK, alignment=TA_LEFT)

        elements = []
        config = FormConfig.objects.filter(is_active=True).first()

        logo_cell = None
        logo_size = 65
        if config and config.logo:
            try:
                from io import BytesIO
                config.logo.open('rb'); img_data = BytesIO(config.logo.read()); logo_raw = RLImage(img_data, width=logo_size, height=logo_size); logo_raw.hAlign = "LEFT"; logo_cell = logo_raw; config.logo.close()
            except: pass
        if not logo_cell:
            logo_path = os.path.join(settings.BASE_DIR, "static", "imgs", "logo.png")
            if os.path.exists(logo_path): logo_raw = RLImage(logo_path, width=logo_size, height=logo_size); logo_raw.hAlign = "LEFT"; logo_cell = logo_raw
        if not logo_cell:
            ph = Paragraph("LOGO", ParagraphStyle("ph", fontSize=7, fontName="Helvetica-Bold", textColor=C_GRAY_LIGHT, alignment=TA_CENTER))
            logo_cell = Table([[ph]], colWidths=[logo_size], rowHeights=[logo_size], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

        # Utiliser les informations de l'établissement choisi si disponible
        from campus.models import Etablissement
        etab_obj = Etablissement.objects.filter(nom=inscription.target_etablissement).first()
        
        school_name = config.school_name if config else "ÉCOLE SUPÉRIEURE DE TECHNOLOGIE, D'INGÉNIERIE ET DE<br/>MANAGEMENT"
        school_agreement = etab_obj.agrement if etab_obj and etab_obj.agrement else (config.school_agreement if config else "Agrément N° 0238 /MES-CAB-DGESUP")
        school_address = etab_obj.adresse if etab_obj and etab_obj.adresse else (config.school_address if config else "91 rue Moulla, croisement av. de la Tsiemé — face Poste Réf / Rond-Point Koulounda — Brazzaville")
        school_contacts = f"Tél : {config.school_phone}  ·  WhatsApp : {config.school_whatsapp}  ·  {config.school_website}" if config else "Tél : 06 966 48 98  ·  WhatsApp : +242 05 559 87 27  ·  www.estim-ecole.com"

        header_texts = [Paragraph(school_name, s_title_header), Spacer(1, 1), Paragraph(school_agreement, s_agrement), Spacer(1, 2), Paragraph(school_address, s_address_header), Paragraph(school_contacts, s_address_header)]
        if is_admin:
            badge_t = Table([[Paragraph("COPIE ADMINISTRATIVE", s_admin_badge)]], colWidths=[100], rowHeights=[13], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), C_ADMIN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
            header_texts.append(Spacer(1, 4)); header_texts.append(badge_t)

        elements.append(Table([[logo_cell, header_texts]], colWidths=[logo_size + 10, usable_w - logo_size - 10], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0)])))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"FICHE D'INSCRIPTION — Session {inscription.annee_academique or '2025-2026'}", s_subtitle))
        elements.append(Spacer(1, 2)); elements.append(HRFlowable(width="100%", thickness=0.4, color=C_GREEN_LIGHT)); elements.append(HRFlowable(width="100%", thickness=1.6, color=C_GOLD, spaceAfter=7))

        etab_para = [Paragraph(f"<b>Établissement :</b> {inscription.target_etablissement or '—'}", s_etab), Spacer(1, 4), Paragraph(f"<b>ID ÉTUDIANT :</b> {inscription.student_id or inscription.pk}", s_etab)]
        photo_cell = None; has_photo = False
        if inscription.photo:
            try:
                from io import BytesIO
                inscription.photo.open('rb'); img_data = BytesIO(inscription.photo.read()); p_img = RLImage(img_data, width=78, height=102); p_img.hAlign = "CENTER"; photo_cell = p_img; has_photo = True; inscription.photo.close()
            except: pass
        if not has_photo:
            ph_txt = Paragraph("PHOTO", ParagraphStyle("phP", fontSize=6, fontName="Helvetica-Bold", textColor=C_GRAY_LIGHT, alignment=TA_CENTER))
            photo_cell = Table([[ph_txt]], colWidths=[78], rowHeights=[102], style=TableStyle([("BOX", (0, 0), (-1, -1), 0.4, C_GRAY_PALE), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        photo_frame = Table([[photo_cell]], colWidths=[86], rowHeights=[110], style=TableStyle([("BOX", (0, 0), (-1, -1), 1, C_GREEN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        elements.append(Table([[etab_para, photo_frame]], colWidths=[usable_w - 94, 86], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])))
        elements.append(Spacer(1, 8))

        def row(label, value): return [Paragraph(label, s_label), Paragraph(str(value) if value else "—", s_value_mono)]
        def row4(l1, v1, l2, v2): return [Paragraph(l1, s_label), Paragraph(str(v1) if v1 else "—", s_value_mono), Paragraph(l2, s_label), Paragraph(str(v2) if v2 else "—", s_value_mono)]
        def section_header(text): return [[Paragraph(text, s_section)]]
        def apply_section_style(table_obj, num_rows):
            cmds = [("BACKGROUND", (0, 0), (-1, 0), C_GREEN_DARK), ("SPAN", (0, 0), (-1, 0)), ("TOPPADDING", (0, 0), (-1, 0), 5), ("BOTTOMPADDING", (0, 0), (-1, 0), 5), ("LEFTPADDING", (0, 0), (-1, 0), 8), ("TOPPADDING", (0, 1), (-1, -1), 4), ("BOTTOMPADDING", (0, 1), (-1, -1), 4), ("LEFTPADDING", (0, 1), (-1, -1), 6), ("RIGHTPADDING", (0, 1), (-1, -1), 6), ("GRID", (0, 0), (-1, -1), 0.35, C_GRAY_PALE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, 0), 1.5, C_GOLD)]
            for i in range(1, num_rows):
                if i % 2 == 0: cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
            table_obj.setStyle(TableStyle(cmds))

        ident_data = section_header("I. IDENTITÉ")
        ident_data.append(row("Nom(s)", inscription.last_name)); ident_data.append(row("Prénom(s)", inscription.first_name))
        ident_data.append(row("Date / Lieu de naiss.", f"{inscription.dob or '—'}  —  {inscription.pob or '—'}"))
        ident_data.append(row("Sexe", "Masculin" if inscription.sexe == "M" else "Féminin"))
        ident_data.append(row("Nationalité", inscription.nationalite)); ident_data.append(row("Téléphone (WhatsApp)", inscription.phone))
        ident_data.append(row("Email", inscription.email or "Non fourni")); ident_data.append(row("Adresse", inscription.adresse))
        t_ident = Table(ident_data, colWidths=[140, usable_w - 140]); apply_section_style(t_ident, len(ident_data)); elements.append(t_ident); elements.append(Spacer(1, 4))

        sit_data = section_header("II. SITUATION CIVILE & TUTEUR")
        sit_data.append(row4("Statut matrimonial", inscription.civil, "Occupation", inscription.occupation))
        sit_data.append(row4("Nom du tuteur", inscription.tuteur, "Tél. tuteur", inscription.tel_tuteur))
        col4 = [92, usable_w / 2 - 92, 92, usable_w / 2 - 92]; t_sit = Table(sit_data, colWidths=col4); apply_section_style(t_sit, len(sit_data)); elements.append(t_sit); elements.append(Spacer(1, 4))

        etu_data = section_header("III. ÉTUDES ANTÉRIEURES")
        etu_data.append(row4("Série du BAC", inscription.bac_serie, "Année obt.", inscription.bac_annee))
        etu_data.append(row4("Étab. du BAC", inscription.bac_etablissement, "Option", inscription.dernier_option))
        etu_data.append(row4("Dernier étab.", inscription.dernier_etab, "Année", inscription.dernier_annee))
        t_etu = Table(etu_data, colWidths=col4); apply_section_style(t_etu, len(etu_data)); elements.append(t_etu); elements.append(Spacer(1, 4))

        choi_data = section_header("IV. CHOIX DE FORMATION")
        choi_data.append(row4("Cycle souhaité", inscription.choix_cycle, "Niv. informatique", inscription.info_level))
        choi_data.append(row4("Filière principale", inscription.choix_filiere, "Filière alt.", inscription.alternative_filiere or "Aucune"))
        t_choi = Table(choi_data, colWidths=col4); apply_section_style(t_choi, len(choi_data)); elements.append(t_choi); elements.append(Spacer(1, 6))

        if is_admin:
            def arow(label, value): return [Paragraph(label, s_admin_label), Paragraph(str(value) if value else "—", s_admin_value)]
            admin_rows = [arow("ID interne", str(inscription.pk)), arow("Date de création", inscription.created_at.strftime("%d/%m/%Y %H:%M:%S"))]
            admin_body = Table(admin_rows, colWidths=[100, usable_w - 100], style=TableStyle([("GRID", (0, 0), (-1, -1), 0.3, C_ADMIN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            elements.append(admin_body); elements.append(Spacer(1, 6))

        sig_line = HRFlowable(width="78%", thickness=0.5, color=C_GRAY_LIGHT, spaceAfter=2, spaceBefore=20)
        sig_left = [Paragraph("Signature de l'étudiant(e)", s_sig_label), sig_line, Paragraph(f"<b>{inscription.last_name or ''} {inscription.first_name or ''}</b>", s_sig_name)]
        sig_right = [Paragraph("Signature & Cachet de l'administration", s_sig_label), sig_line, Spacer(1, 2), Paragraph("Cachet de l'établissement", s_sig_name)]
        elements.append(Table([[sig_left, sig_right]], colWidths=[usable_w/2, usable_w/2], style=TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")])))
        elements.append(Spacer(1, 10))

        # ════════════════════════════════════════════════════════
        # QR CODES (VÉRIFICATION + APPLICATION)
        # ════════════════════════════════════════════════════════
        elements.append(Spacer(1, 10))
        
        try:
            # 1. QR Code de Vérification Digitale
            verify_url = request.build_absolute_uri(reverse("verify_inscription", args=[inscription.pk]))
            qr_v_api = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(verify_url)}&color=1a6b3c&bgcolor=f8faf8"
            
            # 2. QR Code de Téléchargement App
            app_url = config.app_download_url if config and config.app_download_url else "http://www.estim-ecole.com"
            qr_a_api = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={urllib.parse.quote(app_url)}&color=c8960a&bgcolor=f8faf8"
            
            context = ssl._create_unverified_context()
            
            # Récupération QR Vérification
            with urllib.request.urlopen(qr_v_api, timeout=10, context=context) as resp:
                qr_v_img = RLImage(io.BytesIO(resp.read()), width=50, height=50)
            
            # Récupération QR Application
            with urllib.request.urlopen(qr_a_api, timeout=10, context=context) as resp:
                qr_a_img = RLImage(io.BytesIO(resp.read()), width=50, height=50)

            # Construction de la table (2 colonnes de QR + Texte)
            qr_row = [
                qr_v_img, Paragraph("<b>VÉRIFICATION DIGITALE</b><br/>Scannez pour vérifier l'authenticité<br/>de cette fiche d'inscription.", s_qr_text),
                qr_a_img, Paragraph("<b>APPLICATION MOBILE</b><br/>Scannez pour télécharger l'app<br/>officielle ESTIM Campus.", s_qr_text)
            ]
            
            final_qr_table = Table([qr_row], colWidths=[55, usable_w/2 - 60, 55, usable_w/2 - 60])
            final_qr_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            qr_footer_block = Table([[final_qr_table]], colWidths=[usable_w])
            qr_footer_block.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, C_GREEN_LIGHT),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8faf8")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(qr_footer_block)
            
        except Exception as e:
            print(f"QR Code Generation Error: {e}")
            # Fallback simple si l'API QR échoue
            elements.append(Paragraph(f"<font color='red'>Service QR Code momentanément indisponible</font>", s_qr_text))

        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=0.4, color=C_GRAY_PALE))
        ref_text = f"Réf: {inscription.target_etablissement or 'XX'}-{str(inscription.student_id or inscription.pk)} — Généré le {inscription.created_at.strftime('%d/%m/%Y à %H:%M')}"
        elements.append(Paragraph(ref_text, s_ref))

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Fiche_Inscription_{inscription.last_name}.pdf"'
        return response

def inscription_form(request):
    config = FormConfig.objects.filter(is_active=True).first()
    return render(request, "inscription/index.html", {"config": config})
