# Perso d'abord, cœur compatible SaaS

Le projet a une ambition SaaS (proposer le service à d'autres étudiants), mais le besoin immédiat est personnel et urgent : trouver un logement CROUS à Lyon. Nous avons décidé de livrer une v1 mono-utilisateur, tout en modelant le cœur autour du concept de **surveillance** (zone + canal de notification) : le moniteur exécute une *liste* de surveillances, qui n'a qu'un élément en v1.

C'est pourquoi le code contient une abstraction apparemment superflue pour un seul utilisateur : elle est délibérée. Le passage au SaaS consistera à ajouter comptes, persistance partagée (SQLite → Postgres) et gestion de quota de requêtes vers le CROUS — sans réécrire le cœur. Ont été rejetés : le SaaS immédiat (retarderait de plusieurs semaines la première alerte) et le perso-pour-toujours (bloquerait l'ambition affichée).
