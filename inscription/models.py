from django.db import models

class FormConfig(models.Model):
    title = models.CharField(max_length=200, default="ESTIM - Inscription en Ligne")
    annee_academique = models.CharField(max_length=20, default="2025-2026", verbose_name="Année Académique")
    side_image = models.ImageField(upload_to="form_assets/", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Inscription(models.Model):
    # Branch Selection
    target_etablissement = models.CharField(max_length=255, verbose_name="ESTIM d'inscription")
    annee_academique = models.CharField(max_length=20, null=True, blank=True, verbose_name="Année Académique")
    
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

    def save(self, *args, **kwargs):
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
