import json

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Etablissement(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    adresse = models.TextField(null=True, blank=True, verbose_name="Adresse de l'établissement")
    agrement = models.CharField(max_length=255, null=True, blank=True, verbose_name="Agrément de l'établissement")

    def __str__(self):
        return self.nom


class Niveau(models.Model):
    nom = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nom


class Filiere(models.Model):
    nom = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.nom


class Annonce(models.Model):
    TYPE_CHOICES = [
        ("Tous", "Tous"),
        ("Événements", "Événements"),
        ("Cours", "Cours"),
        ("Examens", "Examens"),
        ("Divers", "Divers"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="Divers")
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image = models.ImageField(upload_to="annonces/", null=True, blank=True)

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return self.title


class Cours(models.Model):
    DAY_CHOICES = [
        (i, name)
        for i, name in enumerate(
            [
                "",
                "Lundi",
                "Mardi",
                "Mercredi",
                "Jeudi",
                "Vendredi",
                "Samedi",
                "Dimanche",
            ]
        )
        if i > 0
    ]
    matiere = models.CharField(max_length=200)
    prof = models.CharField(max_length=200)
    salle = models.CharField(max_length=100)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    heure = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.matiere} - {self.niveau}"


class CampusApp(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon_name = models.CharField(max_length=100)
    image_url = models.URLField(max_length=500)
    route = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title


class HeroImage(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    image = models.ImageField(upload_to="hero/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url

    def __str__(self):
        return self.title or f"Hero {self.id}"


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    annonce = models.ForeignKey(
        Annonce, on_delete=models.CASCADE, null=True, blank=True
    )

    # Ajout pour différencier le type de notification
    notification_type = models.CharField(
        max_length=50, default="general"
    )  # 'annonce', 'cours'
    related_id = models.IntegerField(
        null=True, blank=True
    )  # ID de l'annonce ou du cours
    target_matricule = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Matricule cible"
    )

    def __str__(self):
        return self.title


class SessionExamen(models.Model):
    nom = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    results_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class Resultat(models.Model):
    session = models.ForeignKey(
        SessionExamen, on_delete=models.CASCADE, related_name="resultats", null=True
    )
    matricule = models.CharField(max_length=50)
    nom_etudiant = models.CharField(max_length=200)
    moyenne = models.DecimalField(max_digits=4, decimal_places=2)
    admis = models.BooleanField(default=False)
    details_notes = models.JSONField(default=dict)  # {"Maths": 15, "Physique": 12}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("matricule", "session")

    def __str__(self):
        return f"{self.nom_etudiant} ({self.matricule}) - {self.session.nom if self.session else 'No Session'}"


class Transaction(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "En attente"),
        ("SUCCESS", "Réussi"),
        ("FAILED", "Échoué"),
    ]
    payer_matricule = models.CharField(max_length=50)
    target_matricule = models.CharField(max_length=50)
    session = models.ForeignKey(SessionExamen, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_ref = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.payer_matricule} -> {self.target_matricule} ({self.status})"


class Paiement(models.Model):
    payer_matricule = models.CharField(max_length=50, verbose_name="Matricule Payeur")
    target_matricule = models.CharField(max_length=50, verbose_name="Matricule Cible")
    session = models.ForeignKey(SessionExamen, on_delete=models.CASCADE, verbose_name="Session", null=True, blank=True)
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence Paiement")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    payment_method = models.CharField(max_length=50, null=True, blank=True, verbose_name="Méthode de Paiement")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de Paiement")

    class Meta:
        verbose_name = "Paiement Réussi"
        verbose_name_plural = "Paiements Réussis"

    def __str__(self):
        return f"{self.payer_matricule} payé pour {self.target_matricule} - {self.reference}"


class Examen(models.Model):
    TYPE_CHOICES = [
        ("Examen", "Examen"),
        ("Devoir", "Devoir"),
        ("Rattrapage", "Rattrapage"),
        ("Session", "Session"),
        ("Autres", "Autres"),
    ]
    matiere = models.CharField(max_length=200)
    date = models.DateField()
    heure = models.TimeField()
    salle = models.CharField(max_length=100)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="Examen")

    def __str__(self):
        return f"{self.type} - {self.matiere} ({self.date})"


class CalendrierAcademique(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre de l'événement")
    description = models.TextField(verbose_name="Description", blank=True)
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin", null=True, blank=True)
    is_important = models.BooleanField(default=False, verbose_name="Important")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Calendrier Académique"
        verbose_name_plural = "Calendrier Académique"
        ordering = ['date_debut']

    def __str__(self):
        return f"{self.title} ({self.date_debut})"


class SiteWeb(models.Model):
    title = models.CharField(max_length=100, verbose_name="Nom du site")
    url = models.URLField(max_length=500, verbose_name="URL du site")
    icon_name = models.CharField(max_length=50, default="public", verbose_name="Nom de l'icône Material")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lien Site Web"
        verbose_name_plural = "Liens Sites Web"

    def __str__(self):
        return self.title


@receiver(post_save, sender=Annonce)
def create_notification_on_annonce(sender, instance, created, **kwargs):
    if created:
        # Ne pas créer de notification sans target_matricule
        # Pour les annonces, on ne peut pas déterminer un matricule unique
        # donc on ne crée pas de notification générale
        pass


@receiver(post_save, sender=Cours)
def create_notification_on_cours(sender, instance, created, **kwargs):
    if created:
        # Ne pas créer de notification sans target_matricule
        # Pour les cours, on ne peut pas déterminer un matricule unique
        # donc on ne crée pas de notification générale
        pass


@receiver(post_save, sender=Examen)
def create_notification_on_examen(sender, instance, created, **kwargs):
    if created:
        # Ne pas créer de notification sans target_matricule
        # Pour les examens, on ne peut pas déterminer un matricule unique
        # donc on ne crée pas de notification générale
        pass


@receiver(post_save, sender=Resultat)
def create_notification_on_resultat(sender, instance, created, **kwargs):
    if created:
        # Créer notification UNIQUEMENT si matricule est présent
        if instance.matricule:
            Notification.objects.create(
                title=f"🎓 Nouveau résultat disponible",
                message=f"Félicitations {instance.nom_etudiant}, votre résultat pour la session {instance.session.nom} est disponible !",
                notification_type="resultat",
                related_id=instance.id,
                target_matricule=instance.matricule,
            )


@receiver(post_save, sender=CalendrierAcademique)
def create_notification_on_calendrier(sender, instance, created, **kwargs):
    if created:
        # Ne pas créer de notification sans target_matricule
        # Pour le calendrier, on ne peut pas déterminer un matricule unique
        # donc on ne crée pas de notification générale
        pass
