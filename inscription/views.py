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
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import FormConfig, Inscription
from .serializers import InscriptionSerializer


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

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        import io
        import os
        import ssl
        import urllib.parse
        import urllib.request

        from django.conf import settings
        from django.urls import reverse
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

        # ── Mode administratif ─────────────────────────────────
        is_admin = request.query_params.get("admin") == "1"
        if is_admin and not (request.user and request.user.is_staff):
            return Response(
                {"detail": "Accès administratif non autorisé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        buffer = io.BytesIO()
        page_w, page_h = A4  # 595.27 x 841.89
        usable_w = page_w - 28 - 28  # 539.27

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=28,
            leftMargin=28,
            topMargin=20,
            bottomMargin=18,
        )

        # ── COULEURS ────────────────────────────────────────────
        C_GREEN = colors.HexColor("#1a6b3c")
        C_GREEN_DARK = colors.HexColor("#145530")
        C_GREEN_LIGHT = colors.HexColor("#e8f5e9")
        C_GOLD = colors.HexColor("#c8960a")
        C_GOLD_LIGHT = colors.HexColor("#fdf6e3")
        C_DARK = colors.HexColor("#1a2332")
        C_GRAY_DARK = colors.HexColor("#555555")
        C_GRAY = colors.HexColor("#777777")
        C_GRAY_LIGHT = colors.HexColor("#999999")
        C_GRAY_PALE = colors.HexColor("#d0d7de")
        C_ROW_ALT = colors.HexColor("#f6f9f6")
        C_WHITE = colors.white
        C_ADMIN = colors.HexColor("#c62828")
        C_ADMIN_BG = colors.HexColor("#fff5f5")

        # ── STYLES ──────────────────────────────────────────────
        s_title_header = ParagraphStyle(
            "sTitleH",
            fontSize=12.5,
            leading=15,
            fontName="Helvetica-Bold",
            textColor=C_GREEN,
            alignment=TA_CENTER,
            spaceAfter=1,
        )
        s_agrement = ParagraphStyle(
            "sAgrement",
            fontSize=7.5,
            leading=9.5,
            fontName="Helvetica-BoldOblique",
            textColor=C_GRAY_DARK,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s_address_header = ParagraphStyle(
            "sAddrH",
            fontSize=6.5,
            leading=8.5,
            fontName="Helvetica",
            textColor=C_GRAY,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        s_subtitle = ParagraphStyle(
            "sSub",
            fontSize=10.5,
            leading=13,
            fontName="Helvetica-Bold",
            textColor=C_GOLD,
            alignment=TA_CENTER,
            spaceAfter=1,
        )
        s_etab = ParagraphStyle(
            "sEtab",
            fontSize=9,
            leading=12,
            fontName="Helvetica-Bold",
            textColor=C_DARK,
            alignment=TA_LEFT,
            spaceAfter=0,
        )
        s_section = ParagraphStyle(
            "sSec",
            fontSize=8,
            leading=10,
            fontName="Helvetica-Bold",
            textColor=C_WHITE,
            alignment=TA_LEFT,
            spaceAfter=0,
        )
        s_label = ParagraphStyle(
            "sLabel",
            fontSize=7,
            leading=9.5,
            fontName="Helvetica-Bold",
            textColor=C_GREEN,
            alignment=TA_LEFT,
        )
        s_value = ParagraphStyle(
            "sValue",
            fontSize=7.5,
            leading=9.5,
            fontName="Helvetica",
            textColor=C_DARK,
            alignment=TA_LEFT,
        )
        s_value_mono = ParagraphStyle(
            "sValM",
            fontSize=7.5,
            leading=9.5,
            fontName="Courier",
            textColor=C_DARK,
            alignment=TA_LEFT,
        )
        s_sig_label = ParagraphStyle(
            "sSig",
            fontSize=6.5,
            leading=8,
            fontName="Helvetica",
            textColor=C_GRAY,
            alignment=TA_CENTER,
        )
        s_sig_name = ParagraphStyle(
            "sSigN",
            fontSize=7.5,
            leading=9,
            fontName="Helvetica-Bold",
            textColor=C_DARK,
            alignment=TA_CENTER,
        )
        s_footer = ParagraphStyle(
            "sFoot",
            fontSize=6.5,
            leading=8,
            fontName="Helvetica-BoldOblique",
            textColor=C_GOLD,
            alignment=TA_CENTER,
        )
        s_ref = ParagraphStyle(
            "sRef",
            fontSize=6,
            leading=7.5,
            fontName="Helvetica",
            textColor=C_GRAY_LIGHT,
            alignment=TA_RIGHT,
        )
        s_qr_text = ParagraphStyle(
            "QRText",
            fontSize=5.5,
            leading=7.5,
            textColor=C_GRAY,
            alignment=TA_LEFT,
        )
        s_admin_badge = ParagraphStyle(
            "sAdmBadge",
            fontSize=6,
            leading=7,
            fontName="Helvetica-Bold",
            textColor=C_WHITE,
            alignment=TA_CENTER,
        )
        s_admin_label = ParagraphStyle(
            "sAdmLbl",
            fontSize=6,
            leading=7.5,
            fontName="Helvetica-Bold",
            textColor=C_ADMIN,
            alignment=TA_LEFT,
        )
        s_admin_value = ParagraphStyle(
            "sAdmVal",
            fontSize=6.5,
            leading=8,
            fontName="Helvetica",
            textColor=C_GRAY_DARK,
            alignment=TA_LEFT,
        )

        elements = []

        # ════════════════════════════════════════════════════════
        # HEADER — Logo à gauche, texte à droite (sans encadrement)
        # ════════════════════════════════════════════════════════
        logo_path = os.path.join(settings.BASE_DIR, "static", "imgs", "logo.png")
        logo_size = 65
        logo_cell = None

        if os.path.exists(logo_path):
            logo_raw = RLImage(logo_path, width=logo_size, height=logo_size)
            logo_raw.hAlign = "LEFT"
            logo_cell = logo_raw
        else:
            ph = Paragraph(
                "LOGO",
                ParagraphStyle(
                    "ph",
                    fontSize=7,
                    fontName="Helvetica-Bold",
                    textColor=C_GRAY_LIGHT,
                    alignment=TA_CENTER,
                ),
            )
            logo_cell = Table([[ph]], colWidths=[logo_size], rowHeights=[logo_size])
            logo_cell.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))

        header_texts = [
            Paragraph(
                "ÉCOLE SUPÉRIEURE DE TECHNOLOGIE, D'INGÉNIERIE ET DE<br/>MANAGEMENT",
                s_title_header,
            ),
            Spacer(1, 1),
            Paragraph("Agrément N° 0238 /MES-CAB-DGESUP", s_agrement),
            Spacer(1, 2),
            Paragraph(
                "91 rue Moulla, croisement av. de la Tsiemé — face Poste Réf / Rond-Point Koulounda — Brazzaville",
                s_address_header,
            ),
            Paragraph(
                "Tél : 06 966 48 98  ·  WhatsApp : +242 05 559 87 27  ·  www.estim-ecole.com",
                s_address_header,
            ),
        ]

        # Badge admin dans le header
        if is_admin:
            badge_t = Table(
                [[Paragraph("COPIE ADMINISTRATIVE", s_admin_badge)]],
                colWidths=[100],
                rowHeights=[13],
            )
            badge_t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), C_ADMIN),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            header_texts.append(Spacer(1, 4))
            header_texts.append(badge_t)

        text_w = usable_w - logo_size - 15
        header_table = Table(
            [[logo_cell, header_texts]],
            colWidths=[logo_size + 10, text_w],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 8))

        # ════════════════════════════════════════════════════════
        # TITRE — double filet vert clair + doré
        # ════════════════════════════════════════════════════════
        elements.append(
            Paragraph(
                f"FICHE D'INSCRIPTION — Session {inscription.annee_academique or '2025-2026'}",
                s_subtitle,
            )
        )
        elements.append(Spacer(1, 2))
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.4,
                color=C_GREEN_LIGHT,
                spaceAfter=0,
                spaceBefore=0,
            )
        )
        elements.append(
            HRFlowable(
                width="100%", thickness=1.6, color=C_GOLD, spaceAfter=7, spaceBefore=0
            )
        )

        # ════════════════════════════════════════════════════════
        # ÉTABLISSEMENT + PHOTO encadrée
        # ════════════════════════════════════════════════════════
        etab_para = Paragraph(
            f"<b>Établissement :</b> {inscription.target_etablissement or '—'}",
            s_etab,
        )

        photo_cell = None
        has_photo = False
        if inscription.photo:
            try:
                photo_path = inscription.photo.path
                if os.path.exists(photo_path):
                    p_img = RLImage(photo_path, width=78, height=102)
                    p_img.hAlign = "CENTER"
                    photo_cell = p_img
                    has_photo = True
            except Exception:
                pass

        if not has_photo:
            ph_txt = Paragraph(
                "PHOTO",
                ParagraphStyle(
                    "phP",
                    fontSize=6,
                    fontName="Helvetica-Bold",
                    textColor=C_GRAY_LIGHT,
                    alignment=TA_CENTER,
                ),
            )
            ph_tbl = Table([[ph_txt]], colWidths=[78], rowHeights=[102])
            ph_tbl.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.4, C_GRAY_PALE),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            photo_cell = ph_tbl

        # Encadrer la photo
        photo_frame = Table(
            [[photo_cell]],
            colWidths=[86],
            rowHeights=[110],
        )
        photo_frame.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, C_GREEN),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        etab_w = usable_w - 86 - 8
        header_sub_table = Table(
            [[etab_para, photo_frame]],
            colWidths=[etab_w, 86],
        )
        header_sub_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(header_sub_table)
        elements.append(Spacer(1, 8))

        # ════════════════════════════════════════════════════════
        # HELPERS
        # ════════════════════════════════════════════════════════
        def row(label, value):
            return [
                Paragraph(label, s_label),
                Paragraph(str(value) if value else "—", s_value_mono),
            ]

        def row4(l1, v1, l2, v2):
            return [
                Paragraph(l1, s_label),
                Paragraph(str(v1) if v1 else "—", s_value_mono),
                Paragraph(l2, s_label),
                Paragraph(str(v2) if v2 else "—", s_value_mono),
            ]

        def section_header(text):
            return [[Paragraph(text, s_section)]]

        def apply_section_style(table_obj, num_rows):
            """Applique le style standardisé à une section."""
            cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), C_GREEN_DARK),
                ("SPAN", (0, 0), (-1, 0)),
                ("TOPPADDING", (0, 0), (-1, 0), 5),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("LEFTPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ("LEFTPADDING", (0, 1), (-1, -1), 6),
                ("RIGHTPADDING", (0, 1), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.35, C_GRAY_PALE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, C_GOLD),
            ]
            # Alternance de couleurs sur les lignes de données
            for i in range(1, num_rows):
                if i % 2 == 0:
                    cmds.append(("BACKGROUND", (0, i), (-1, i), C_ROW_ALT))
            table_obj.setStyle(TableStyle(cmds))

        # ════════════════════════════════════════════════════════
        # I. IDENTITÉ
        # ════════════════════════════════════════════════════════
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

        t_ident = Table(ident_data, colWidths=[140, usable_w - 140])
        apply_section_style(t_ident, len(ident_data))
        elements.append(t_ident)
        elements.append(Spacer(1, 4))

        # ════════════════════════════════════════════════════════
        # II. SITUATION CIVILE & TUTEUR
        # ════════════════════════════════════════════════════════
        civil_text = inscription.civil or "—"
        occ_text = inscription.occupation or "—"
        if inscription.profession:
            occ_text += f" ({inscription.profession})"

        sit_data = section_header("II. SITUATION CIVILE & TUTEUR")
        sit_data.append(row4("Statut matrimonial", civil_text, "Occupation", occ_text))
        sit_data.append(
            row4(
                "Nom du tuteur",
                inscription.tuteur,
                "Tél. tuteur",
                inscription.tel_tuteur,
            )
        )

        col4 = [92, usable_w / 2 - 92, 92, usable_w / 2 - 92]
        t_sit = Table(sit_data, colWidths=col4)
        apply_section_style(t_sit, len(sit_data))
        elements.append(t_sit)
        elements.append(Spacer(1, 4))

        # ════════════════════════════════════════════════════════
        # III. ÉTUDES ANTÉRIEURES
        # ════════════════════════════════════════════════════════
        etu_data = section_header("III. ÉTUDES ANTÉRIEURES")
        etu_data.append(
            row4(
                "Série du BAC",
                inscription.bac_serie,
                "Année obt.",
                inscription.bac_annee,
            )
        )
        etu_data.append(
            row4(
                "Étab. du BAC",
                inscription.bac_etablissement,
                "Option",
                inscription.dernier_option,
            )
        )
        etu_data.append(
            row4(
                "Dernier étab.",
                inscription.dernier_etab,
                "Année",
                inscription.dernier_annee,
            )
        )

        t_etu = Table(etu_data, colWidths=col4)
        apply_section_style(t_etu, len(etu_data))
        elements.append(t_etu)
        elements.append(Spacer(1, 4))

        # ════════════════════════════════════════════════════════
        # IV. CHOIX DE FORMATION
        # ════════════════════════════════════════════════════════
        choi_data = section_header("IV. CHOIX DE FORMATION")
        choi_data.append(
            row4(
                "Cycle souhaité",
                inscription.choix_cycle,
                "Niv. informatique",
                inscription.info_level,
            )
        )
        choi_data.append(
            row4(
                "Filière principale",
                inscription.choix_filiere,
                "Filière alt.",
                inscription.alternative_filiere or "Aucune",
            )
        )

        t_choi = Table(choi_data, colWidths=col4)
        apply_section_style(t_choi, len(choi_data))
        elements.append(t_choi)
        elements.append(Spacer(1, 6))

        # ════════════════════════════════════════════════════════
        # SECTION ADMIN (si activée)
        # ════════════════════════════════════════════════════════
        if is_admin:

            def arow(label, value):
                return [
                    Paragraph(label, s_admin_label),
                    Paragraph(str(value) if value else "—", s_admin_value),
                ]

            admin_hdr = Table(
                [
                    [
                        Paragraph(
                            "INFORMATIONS ADMINISTRATIVES",
                            ParagraphStyle(
                                "admH",
                                fontSize=7,
                                leading=9,
                                fontName="Helvetica-Bold",
                                textColor=C_WHITE,
                                alignment=TA_LEFT,
                            ),
                        )
                    ]
                ],
                colWidths=[usable_w],
            )
            admin_hdr.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), C_ADMIN),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )

            admin_rows = [
                arow("ID interne", str(inscription.pk)),
                arow(
                    "Date de création",
                    inscription.created_at.strftime("%d/%m/%Y %H:%M:%S")
                    if inscription.created_at
                    else "—",
                ),
                arow(
                    "Dernière modification",
                    inscription.updated_at.strftime("%d/%m/%Y %H:%M:%S")
                    if inscription.updated_at
                    else "—",
                ),
                arow("Adresse IP", getattr(inscription, "ip_address", "—")),
            ]
            ua = getattr(inscription, "user_agent", "—")
            if ua and len(ua) > 90:
                ua = ua[:90] + "…"
            admin_rows.append(arow("User-Agent", ua))

            admin_body = Table(admin_rows, colWidths=[100, usable_w - 100])
            admin_cmds = [
                ("GRID", (0, 0), (-1, -1), 0.3, C_ADMIN),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
            for i in range(len(admin_rows)):
                bg = C_ADMIN_BG if i % 2 == 0 else C_WHITE
                admin_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
            admin_body.setStyle(TableStyle(admin_cmds))

            admin_block = Table(
                [[admin_hdr], [admin_body]],
                colWidths=[usable_w],
            )
            admin_block.setStyle(
                TableStyle(
                    [
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            elements.append(admin_block)
            elements.append(Spacer(1, 6))

        # ════════════════════════════════════════════════════════
        # SIGNATURES
        # ════════════════════════════════════════════════════════
        sig_line = HRFlowable(
            width="78%",
            thickness=0.5,
            color=C_GRAY_LIGHT,
            spaceAfter=2,
            spaceBefore=20,
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
            Spacer(1, 2),
            Paragraph("Cachet de l'établissement", s_sig_name),
        ]

        half_w = (usable_w - 16) / 2
        t_sig = Table([[sig_left, sig_right]], colWidths=[half_w, half_w])
        t_sig.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )
        elements.append(t_sig)
        elements.append(Spacer(1, 10))

        # ════════════════════════════════════════════════════════
        # QR CODE
        # ════════════════════════════════════════════════════════
        verify_url = request.build_absolute_uri(
            reverse("verify_inscription", args=[inscription.pk])
        )
        qr_url = (
            f"https://api.qrserver.com/v1/create-qr-code/"
            f"?size=180x180&data={urllib.parse.quote(verify_url)}"
            f"&color=1a6b3c&bgcolor=f8faf8"
        )

        try:
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(qr_url, timeout=20, context=context) as resp:
                qr_io = io.BytesIO(resp.read())
                qr_img = RLImage(qr_io, width=52, height=52)
                qr_img.hAlign = "LEFT"

            qr_para = Paragraph(
                "<b>VÉRIFICATION DIGITALE</b><br/>"
                "Scannez ce QR code pour vérifier<br/>"
                "l'authenticité de cette fiche.",
                s_qr_text,
            )

            qr_inner = Table([[qr_img, qr_para]], colWidths=[58, 120])
            qr_inner.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )

            # Encadrer le bloc QR
            qr_block = Table([[qr_inner]], colWidths=[185])
            qr_block.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.5, C_GREEN_LIGHT),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8faf8")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(qr_block)
        except Exception as e:
            print(f"QR Code generation failed: {e}")

        # ════════════════════════════════════════════════════════
        # FOOTER
        # ════════════════════════════════════════════════════════
        elements.append(Spacer(1, 4))
        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.4,
                color=C_GRAY_PALE,
                spaceAfter=2,
                spaceBefore=4,
            )
        )

        elements.append(Spacer(1, 1))

        ref_text = (
            f"Réf: {inscription.target_etablissement or 'XX'}-"
            f"{str(inscription.pk).zfill(4)} — "
            f"Généré le {inscription.created_at.strftime('%d/%m/%Y à %H:%M') if inscription.created_at else '—'}"
        )
        elements.append(Paragraph(ref_text, s_ref))

        # ── BUILD ───────────────────────────────────────────────
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type="application/pdf")
        safe_name = f"{inscription.last_name or 'inscription'}".replace(" ", "_")
        suffix = "_ADMIN" if is_admin else ""
        response["Content-Disposition"] = (
            f'attachment; filename="Fiche_Inscription_{safe_name}{suffix}.pdf"'
        )
        return response


def inscription_form(request):
    config = FormConfig.objects.filter(is_active=True).first()
    return render(request, "inscription/index.html", {"config": config})
