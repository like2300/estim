import random
import string
from django.db import models

class FormConfig(models.Model):
    title = models.CharField(max_length=200, default="ESTIM - Inscription en Ligne")
    school_name = models.CharField(max_length=255, default="ÉCOLE SUPÉRIEURE DE TECHNOLOGIE, D'INGÉNIERIE ET DE MANAGEMENT", verbose_name="Nom de l'école")
    school_agreement = models.CharField(max_length=255, default="Agrément N° 0238 /MES-CAB-DGESUP", verbose_name="Agrément")
    school_address = models.TextField(default="91 rue Moulla, croisement av. de la Tsiemé — face Poste Réf / Rond-Point Koulounda — Brazzaville", verbose_name="Adresse")
    school_phone = models.CharField(max_length=100, default="+242 061167676", verbose_name="Téléphone")
    school_whatsapp = models.CharField(max_length=100, default="+242 05 559 87 27", verbose_name="WhatsApp")
    school_website = models.URLField(default="http://www.estim-ecole.com", verbose_name="Site Web")
    logo = models.ImageField(upload_to="form_assets/", null=True, blank=True, verbose_name="Logo")
    
    annee_academique = models.CharField(max_length=20, default="2025-2026", verbose_name="Année Académique")
    side_image = models.ImageField(upload_to="form_assets/", null=True, blank=True, verbose_name="Image latérale (Web)")
    is_active = models.BooleanField(default=True)

    # Liens de téléchargement et QR Codes
    app_download_url = models.URLField(max_length=500, blank=True, verbose_name="URL de téléchargement App")
    qrcode_app = models.ImageField(upload_to="form_assets/", null=True, blank=True, verbose_name="QR Code App 1")
    qrcode_app_alternative = models.ImageField(upload_to="form_assets/", null=True, blank=True, verbose_name="QR Code App 2")

    def __str__(self):
        return self.title

class Inscription(models.Model):
    # Branch Selection
    target_etablissement = models.CharField(max_length=255, verbose_name="ESTIM d'inscription")
    annee_academique = models.CharField(max_length=20, null=True, blank=True, verbose_name="Année Académique")
    student_id = models.CharField(max_length=8, unique=True, null=True, blank=True, verbose_name="ID Étudiant")
    photo = models.ImageField(upload_to="inscriptions/photos/", null=True, blank=True, verbose_name="Photo d'identité")
    
    # Identité
    last_name = models.CharField(max_length=255, verbose_name="Nom(s)")
    first_name = models.CharField(max_length=255, verbose_name="Prénom(s)")
    dob = models.DateField(verbose_name="Date de naissance")
    pob = models.CharField(max_length=255, verbose_name="Lieu de naissance")
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    nationalite = models.CharField(max_length=100, verbose_name="Nationalité")
    phone = models.CharField(max_length=20, verbose_name="Téléphone / WhatsApp")
    email = models.EmailField(verbose_name="Email", null=True, blank=True)
    adresse = models.CharField(max_length=255, verbose_name="Adresse")
    tuteur = models.CharField(max_length=255, verbose_name="Nom du tuteur")
    tel_tuteur = models.CharField(max_length=20, verbose_name="Tél. du tuteur")

    # Situation Civile et Professionnelle
    civil = models.CharField(max_length=50, verbose_name="Statut matrimonial")
    occupation = models.CharField(max_length=50, verbose_name="Occupation actuelle")
    profession = models.CharField(max_length=255, verbose_name="Profession / Métier", null=True, blank=True)

    # Études Antérieures
    bac_serie = models.CharField(max_length=50, verbose_name="Baccalauréat série")
    bac_annee = models.CharField(max_length=10, verbose_name="Année d'obtention")
    bac_etablissement = models.CharField(max_length=255, verbose_name="Établissement du BAC")
    dernier_etab = models.CharField(max_length=255, verbose_name="Dernier établissement fréquenté")
    dernier_annee = models.CharField(max_length=10, verbose_name="Année")
    dernier_option = models.CharField(max_length=100, verbose_name="Option (Études précédentes)")

    # Choix de Formation (Principal + Alternative)
    choix_cycle = models.CharField(max_length=100, verbose_name="Cycle souhaité")
    choix_filiere = models.CharField(max_length=255, verbose_name="Filière principale")
    alternative_filiere = models.CharField(max_length=255, verbose_name="Filière alternative", null=True, blank=True)
    
    # Niveau en Informatique
    info_level = models.CharField(max_length=50, verbose_name="Niveau en Informatique", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def generate_student_id(self):
        chars = string.ascii_uppercase + string.digits
        while True:
            new_id = ''.join(random.choice(chars) for _ in range(8))
            if not Inscription.objects.filter(student_id=new_id).exists():
                return new_id

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_student_id()
            
        # Formatage du téléphone
        if self.phone and not self.phone.startswith('+'):
            self.phone = f"+242{self.phone}"
        if self.tel_tuteur and not self.tel_tuteur.startswith('+'):
            self.tel_tuteur = f"+242{self.tel_tuteur}"
        
        # Passage en majuscules (sauf email)
        fields_to_upper = [
            'last_name', 'first_name', 'pob', 'nationalite', 'adresse', 'tuteur', 
            'civil', 'occupation', 'profession', 'bac_serie', 'bac_etablissement', 
            'dernier_etab', 'dernier_option', 'choix_cycle', 'choix_filiere', 
            'alternative_filiere', 'target_etablissement'
        ]
        for field in fields_to_upper:
            val = getattr(self, field)
            if val and isinstance(val, str):
                setattr(self, field, val.upper())
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.target_etablissement})"
