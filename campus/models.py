import json

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Etablissement(models.Model):
    nom = models.CharField(max_length=200, unique=True)

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
    session = models.ForeignKey(SessionExamen, on_delete=models.CASCADE, verbose_name="Session")
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


@receiver(post_save, sender=Annonce)
def create_notification_on_annonce(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            title=f"📢 Nouvelle annonce : {instance.title}",
            message=instance.description[:100] + "...",
            annonce=instance,
            notification_type="annonce",
            related_id=instance.id,
        )


@receiver(post_save, sender=Cours)
def create_notification_on_cours(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            title=f"📅 Nouveau cours : {instance.matiere}",
            message=f"Le cours de {instance.matiere} ({instance.niveau}) a été ajouté à l'emploi du temps.",
            notification_type="cours",
            related_id=instance.id,
        )


@receiver(post_save, sender=Examen)
def create_notification_on_examen(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            title=f"📝 Nouvel examen : {instance.matiere}",
            message=f"Un(e) {instance.type} de {instance.matiere} est prévu le {instance.date} à {instance.heure}.",
            notification_type="examen",
            related_id=instance.id,
        )
