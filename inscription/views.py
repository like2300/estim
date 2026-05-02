import io
import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from reportlab.lib import colors

# PDF Generation imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FormConfig, Inscription
from .serializers import InscriptionSerializer


class InscriptionViewSet(viewsets.ModelViewSet):
    queryset = Inscription.objects.all()
    serializer_class = InscriptionSerializer

    def perform_create(self, serializer):
        config = FormConfig.objects.filter(is_active=True).first()
        annee = config.annee_academique if config else "2025-2026"
        serializer.save(annee_academique=annee)

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        import io
        import os

        from django.conf import settings
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
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

        inscription = get_object_or_404(Inscription, pk=pk)

        buffer = io.BytesIO()
        page_w, page_h = A4  # 595.27 x 841.89

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=28,
            leftMargin=28,
            topMargin=22,
            bottomMargin=22,
        )

        # ── STYLES ──────────────────────────────────────────────
        s_title = ParagraphStyle(
            "sTitle",
            fontSize=11,
            leading=13,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a6b3c"),
            alignment=TA_CENTER,
            spaceAfter=2,
        )
        s_subtitle = ParagraphStyle(
            "sSub",
            fontSize=8.5,
            leading=11,
            fontName="Helvetica",
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=1,
        )
        s_etab = ParagraphStyle(
            "sEtab",
            fontSize=9,
            leading=12,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a2332"),
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s_section = ParagraphStyle(
            "sSec",
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=colors.white,
            alignment=TA_LEFT,
            spaceAfter=0,
        )
        s_label = ParagraphStyle(
            "sLabel",
            fontSize=7.5,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a6b3c"),
            alignment=TA_LEFT,
        )
        s_value = ParagraphStyle(
            "sValue",
            fontSize=8,
            leading=10,
            fontName="Helvetica",
            textColor=colors.HexColor("#1a2332"),
            alignment=TA_LEFT,
        )
        s_value_courier = ParagraphStyle(
            "sValC",
            fontSize=8,
            leading=10,
            fontName="Courier",
            textColor=colors.HexColor("#1a2332"),
            alignment=TA_LEFT,
        )
        s_doc_item = ParagraphStyle(
            "sDoc",
            fontSize=7,
            leading=9.5,
            fontName="Helvetica",
            textColor=colors.HexColor("#333333"),
            alignment=TA_LEFT,
            leftIndent=10,
        )
        s_sig_label = ParagraphStyle(
            "sSig",
            fontSize=7,
            leading=9,
            fontName="Helvetica",
            textColor=colors.HexColor("#777777"),
            alignment=TA_CENTER,
        )
        s_sig_name = ParagraphStyle(
            "sSigN",
            fontSize=7.5,
            leading=9,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1a2332"),
            alignment=TA_CENTER,
        )
        s_footer = ParagraphStyle(
            "sFoot",
            fontSize=7,
            leading=9,
            fontName="Helvetica-BoldOblique",
            textColor=colors.HexColor("#c8960a"),
            alignment=TA_CENTER,
        )
        s_ref = ParagraphStyle(
            "sRef",
            fontSize=6.5,
            leading=8,
            fontName="Helvetica",
            textColor=colors.HexColor("#999999"),
            alignment=TA_RIGHT,
        )

        green = colors.HexColor("#1a6b3c")
        green_light = colors.HexColor("#e8f5e9")
        gold = colors.HexColor("#c8960a")
        border_gray = colors.HexColor("#d0d7de")
        row_alt = colors.HexColor("#f8faf8")

        elements = []

        # ── HEADER ──────────────────────────────────────────────
        # Logo
        logo_path = os.path.join(settings.BASE_DIR, "static", "imgs", "logo.png")
        if os.path.exists(logo_path):
            img = RLImage(logo_path, width=52, height=52)
            img.hAlign = "CENTER"
            elements.append(img)
        else:
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "ÉCOLE SUPÉRIEURE DE TECHNOLOGIE, D'INGÉNIERIE ET DE MANAGEMENT",
                s_title,
            )
        )
        elements.append(
            Paragraph(
                f"FICHE D'INSCRIPTION — Session {inscription.annee_academique or '2025-2026'}",
                s_subtitle,
            )
        )
        elements.append(Spacer(1, 2))
        elements.append(
            HRFlowable(
                width="100%", thickness=1.5, color=green, spaceAfter=3, spaceBefore=0
            )
        )
        elements.append(
            Paragraph(
                f"<b>Établissement :</b> {inscription.target_etablissement or '—'}",
                s_etab,
            )
        )
        elements.append(Spacer(1, 6))

        # ── IDENTITÉ (2 colonnes) ──────────────────────────────
        def row(label, value):
            return [
                Paragraph(label, s_label),
                Paragraph(str(value) if value else "—", s_value_courier),
            ]

        def section_header(text):
            return [[Paragraph(text, s_section)]]

        # Section : Identité
        ident_data = section_header("I. IDENTITÉ")
        ident_data.append(row("Nom(s)", inscription.last_name))
        ident_data.append(row("Prénom(s)", inscription.first_name))
        ident_data.append(
            row(
                "Date / Lieu de naiss.",
                f"{inscription.dob or '—'}  —  {inscription.pob or '—'}",
            )
        )
        ident_data.append(
            row("Sexe", "Masculin" if inscription.sexe == "M" else "Féminin")
        )
        ident_data.append(row("Nationalité", inscription.nationalite))
        ident_data.append(row("Téléphone (WhatsApp)", inscription.phone))
        ident_data.append(row("Email", inscription.email or "Non fourni"))
        ident_data.append(row("Adresse", inscription.adresse))

        t_ident = Table(ident_data, colWidths=[135, 350])
        t_ident.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), green),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.4, border_gray),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, green),
                ]
            )
        )
        elements.append(t_ident)
        elements.append(Spacer(1, 5))

        # Section : Situation (2 colonnes avec identité tuteur)
        sit_data = section_header("II. SITUATION CIVILE & TUTEUR")
        civil_text = inscription.civil or "—"
        occ_text = inscription.occupation or "—"
        if inscription.profession:
            occ_text += f" ({inscription.profession})"
        sit_data.append(
            [
                Paragraph("Statut matrimonial", s_label),
                Paragraph(civil_text, s_value),
                Paragraph("Occupation", s_label),
                Paragraph(occ_text, s_value),
            ]
        )
        sit_data.append(
            [
                Paragraph("Nom du tuteur", s_label),
                Paragraph(inscription.tuteur or "—", s_value_courier),
                Paragraph("Tél. tuteur", s_label),
                Paragraph(inscription.tel_tuteur or "—", s_value_courier),
            ]
        )

        t_sit = Table(sit_data, colWidths=[95, 155, 95, 140])
        t_sit.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), green),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.4, border_gray),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, green),
                ]
            )
        )
        elements.append(t_sit)
        elements.append(Spacer(1, 5))

        # Section : Études (2 colonnes)
        etu_data = section_header("III. ÉTUDES ANTÉRIEURES")
        etu_data.append(
            [
                Paragraph("Série du BAC", s_label),
                Paragraph(inscription.bac_serie or "—", s_value_courier),
                Paragraph("Année obt.", s_label),
                Paragraph(inscription.bac_annee or "—", s_value_courier),
            ]
        )
        etu_data.append(
            [
                Paragraph("Étab. du BAC", s_label),
                Paragraph(inscription.bac_etablissement or "—", s_value_courier),
                Paragraph("Option", s_label),
                Paragraph(inscription.dernier_option or "—", s_value_courier),
            ]
        )
        etu_data.append(
            [
                Paragraph("Dernier étab.", s_label),
                Paragraph(inscription.dernier_etab or "—", s_value_courier),
                Paragraph("Année", s_label),
                Paragraph(inscription.dernier_annee or "—", s_value_courier),
            ]
        )

        t_etu = Table(etu_data, colWidths=[95, 155, 95, 140])
        t_etu.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), green),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.4, border_gray),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, green),
                ]
            )
        )
        elements.append(t_etu)
        elements.append(Spacer(1, 5))

        # Section : Choix formation (2 colonnes)
        choi_data = section_header("IV. CHOIX DE FORMATION")
        choi_data.append(
            [
                Paragraph("Cycle souhaité", s_label),
                Paragraph(inscription.choix_cycle or "—", s_value),
                Paragraph("Niv. informatique", s_label),
                Paragraph(inscription.info_level or "—", s_value),
            ]
        )
        choi_data.append(
            [
                Paragraph("Filière principale", s_label),
                Paragraph(inscription.choix_filiere or "—", s_value_courier),
                Paragraph("Filière alt.", s_label),
                Paragraph(inscription.alternative_filiere or "Aucune", s_value_courier),
            ]
        )

        t_choi = Table(choi_data, colWidths=[95, 155, 95, 140])
        t_choi.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), green),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.4, border_gray),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, green),
                ]
            )
        )
        elements.append(t_choi)
        elements.append(Spacer(1, 6))

        # ── PIÈCES À FOURNIR ───────────────────────────────────
        docs_header = [[Paragraph("V. PIÈCES ADMINISTRATIVES À FOURNIR", s_section)]]
        docs_items = [
            "1.  Original du diplôme ou attestation de réussite au BAC",
            "2.  Relevé de notes du BAC (copie certifiée)",
            "3.  Extrait d'acte de naissance (copie intégrale)",
            "4.  Copie légalisée de la CIN ou passeport",
            "5.  4 photos d'identité récentes format passeport",
            "6.  Si fonctionnaire : attestation d'emploi ou décision de mise en disponibilité",
        ]
        docs_rows = docs_header[:]
        # 2 colonnes de pièces
        half = (len(docs_items) + 1) // 2
        left_docs = docs_items[:half]
        right_docs = docs_items[half:]
        for i in range(max(len(left_docs), len(right_docs))):
            docs_rows.append(
                [
                    Paragraph(left_docs[i] if i < len(left_docs) else "", s_doc_item),
                    Paragraph(right_docs[i] if i < len(right_docs) else "", s_doc_item),
                ]
            )

        t_docs = Table(docs_rows, colWidths=[242, 243])
        t_docs.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5a3e00")),
                    ("SPAN", (0, 0), (-1, 0)),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#5a3e00")),
                    ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#5a3e00")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(t_docs)
        elements.append(Spacer(1, 8))

        # ── SIGNATURES ──────────────────────────────────────────
        sig_line = HRFlowable(
            width="85%",
            thickness=0.6,
            color=colors.HexColor("#999999"),
            spaceAfter=2,
            spaceBefore=22,
        )

        sig_left = [
            Paragraph("Signature de l'étudiant(e)", s_sig_label),
            sig_line,
            Paragraph(
                f"<b>{inscription.last_name or ''} {inscription.first_name or ''}</b>",
                s_sig_name,
            ),
        ]
        sig_right = [
            Paragraph("Signature & Cachet de l'administration", s_sig_label),
            sig_line,
            Paragraph("Cachet", s_sig_name),
        ]

        t_sig = Table([[sig_left, sig_right]], colWidths=[242, 243])
        t_sig.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        elements.append(t_sig)
        elements.append(Spacer(1, 6))

        # ── FOOTER ──────────────────────────────────────────────
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.8,
                color=border_gray,
                spaceAfter=3,
                spaceBefore=0,
            )
        )
        # Référence en bas à droite
        ref_text = f"Réf: ESTIM-{inscription.target_etablissement or 'XX'}-{str(inscription.pk).zfill(4)} — Généré le {inscription.created_at.strftime('%d/%m/%Y %H:%M') if inscription.created_at else '—'}"
        # add margin
        elements.append(Spacer(1, 9))
        elements.append(Paragraph(ref_text, s_ref))

        # ── BUILD ───────────────────────────────────────────────
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        safe_name = f"{inscription.last_name or 'inscription'}".replace(" ", "_")
        response["Content-Disposition"] = (
            f'attachment; filename="Fiche_Inscription_{safe_name}.pdf"'
        )
        return response


def inscription_form(request):
    config = FormConfig.objects.filter(is_active=True).first()
    return render(request, "inscription/index.html", {"config": config})
