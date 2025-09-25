# OptimumSolar

Ce dépôt contient un petit programme de facturation en ligne de commande pour
OptimumSolar, société jurassienne spécialisée dans la gestion de projets et
l'administration des regroupements de consommation propre.

## Prérequis

* Python 3.10 ou plus récent.

## Installation et utilisation

1. Cloner ce dépôt et se placer à sa racine.
2. Lancer le programme :

   ```bash
   python3 billing.py
   ```

3. Suivre les instructions du menu pour :
   * ajouter des clients,
   * créer des factures et générer automatiquement un fichier Markdown dans le
     dossier `invoices/`,
   * consulter la liste des clients et factures enregistrés.

Toutes les données sont stockées dans `data/billing_data.json`. Vous pouvez
sauvegarder ce fichier pour vos archives ou le copier sur un autre poste pour
retrouver vos clients et factures.

## Structure des factures

Chaque facture contient :

* les coordonnées de votre client,
* une liste des prestations fournies (gestion de projet, administration des
  regroupements de consommation propre, etc.),
* le calcul automatique de la TVA suisse (7.7 % par défaut, modifiable lors de
  la création de la facture),
* le total TTC.

Le fichier Markdown généré peut être facilement converti en PDF à l'aide de
Pandoc ou d'un traitement de texte. Vous pouvez également personnaliser le
contenu en éditant le fichier `billing.py` selon vos besoins spécifiques.

## Sauvegarde

Le dossier `invoices/` contient l'ensemble des factures générées. Pensez à le
archiver régulièrement ainsi que le fichier `data/billing_data.json` pour ne
pas perdre votre historique.
