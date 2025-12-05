import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

// Mentions Légales
export const MentionsLegales = () => {
  return (
    <div className="page-container legal-page" data-testid="mentions-legales">
      <div className="page-header">
        <h1>Mentions Légales</h1>
      </div>

      <Card className="legal-card">
        <CardContent>
          <section>
            <h2>1. Éditeur du site</h2>
            <p>
              <strong>Raison sociale :</strong> [À compléter]<br />
              <strong>Forme juridique :</strong> [À compléter]<br />
              <strong>Capital social :</strong> [À compléter]<br />
              <strong>Siège social :</strong> [À compléter]<br />
              <strong>SIRET :</strong> [À compléter]<br />
              <strong>RCS :</strong> [À compléter]<br />
              <strong>N° TVA intracommunautaire :</strong> [À compléter]<br />
              <strong>Email :</strong> [À compléter]<br />
              <strong>Téléphone :</strong> [À compléter]
            </p>
            <p><strong>Directeur de la publication :</strong> [À compléter]</p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>2. Hébergement</h2>
            <p>
              Le site SkiMonitor est hébergé par :<br />
              <strong>Emergent Agent</strong><br />
              [Adresse hébergeur]<br />
              [Contact hébergeur]
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>3. Propriété intellectuelle</h2>
            <p>
              L'ensemble du contenu du site SkiMonitor (textes, images, graphismes, logo, icônes, etc.) 
              est la propriété exclusive de [Nom de la société], à l'exception des marques, logos ou 
              contenus appartenant à d'autres sociétés partenaires ou auteurs.
            </p>
            <p>
              Toute reproduction, distribution, modification, adaptation, retransmission ou publication, 
              même partielle, de ces différents éléments est strictement interdite sans l'accord exprès 
              par écrit de [Nom de la société].
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>4. Limitation de responsabilité</h2>
            <p>
              SkiMonitor s'efforce d'assurer au mieux l'exactitude et la mise à jour des informations 
              diffusées sur ce site. Toutefois, SkiMonitor ne peut garantir l'exactitude, la précision 
              ou l'exhaustivité des informations mises à disposition sur ce site.
            </p>
            <p>
              En conséquence, SkiMonitor décline toute responsabilité :
            </p>
            <ul>
              <li>Pour toute imprécision, inexactitude ou omission portant sur des informations disponibles sur le site</li>
              <li>Pour tous dommages résultant d'une intrusion frauduleuse d'un tiers</li>
              <li>Pour tous dommages, directs ou indirects, quelles qu'en soient les causes, origines, natures ou conséquences</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>5. Cookies</h2>
            <p>
              Le site SkiMonitor utilise des cookies nécessaires à son fonctionnement (authentification, 
              session utilisateur). Ces cookies sont essentiels et ne peuvent pas être désactivés.
            </p>
            <p>
              Aucun cookie publicitaire ou de tracking n'est utilisé sur ce site.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>6. Droit applicable</h2>
            <p>
              Les présentes mentions légales sont régies par le droit français. En cas de litige, 
              les tribunaux français seront seuls compétents.
            </p>
          </section>

          <p className="legal-update">Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}</p>
        </CardContent>
      </Card>
    </div>
  );
};

// Conditions Générales d'Utilisation
export const CGU = () => {
  return (
    <div className="page-container legal-page" data-testid="cgu">
      <div className="page-header">
        <h1>Conditions Générales d'Utilisation</h1>
      </div>

      <Card className="legal-card">
        <CardContent>
          <section>
            <h2>1. Objet</h2>
            <p>
              Les présentes Conditions Générales d'Utilisation (CGU) ont pour objet de définir les 
              conditions d'accès et d'utilisation de la plateforme SkiMonitor, service de mise en 
              relation entre des moniteurs de ski indépendants et des clients souhaitant réserver 
              des cours de ski ou de snowboard.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>2. Acceptation des CGU</h2>
            <p>
              L'utilisation de la plateforme SkiMonitor implique l'acceptation pleine et entière 
              des présentes CGU. Si vous n'acceptez pas ces conditions, vous ne devez pas utiliser 
              la plateforme.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>3. Description du service</h2>
            <p>SkiMonitor est une plateforme de mise en relation qui permet :</p>
            <ul>
              <li>Aux <strong>clients</strong> de rechercher et réserver des cours de ski/snowboard auprès de moniteurs indépendants</li>
              <li>Aux <strong>moniteurs</strong> de proposer leurs services et gérer leurs réservations</li>
            </ul>
            <p>
              SkiMonitor agit uniquement en qualité d'intermédiaire et n'est pas partie au contrat 
              conclu entre le moniteur et le client.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>4. Inscription et compte utilisateur</h2>
            <h3>4.1 Création de compte</h3>
            <p>
              L'accès à certaines fonctionnalités nécessite la création d'un compte via Google OAuth. 
              L'utilisateur s'engage à fournir des informations exactes.
            </p>
            <h3>4.2 Inscription des moniteurs</h3>
            <p>
              Les moniteurs doivent soumettre une demande d'inscription qui sera validée par l'équipe 
              SkiMonitor. Les moniteurs doivent :
            </p>
            <ul>
              <li>Être titulaires des diplômes requis (BEES, DE, ou équivalent)</li>
              <li>Disposer d'une assurance responsabilité civile professionnelle valide</li>
              <li>Être en règle avec leurs obligations légales et fiscales</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>5. Réservation et paiement</h2>
            <h3>5.1 Processus de réservation</h3>
            <p>
              Le client choisit un cours disponible et effectue une réservation. La réservation 
              est confirmée après paiement en ligne.
            </p>
            <h3>5.2 Prix et commission</h3>
            <p>
              Les prix sont fixés librement par les moniteurs. SkiMonitor prélève une commission 
              de 10% sur chaque transaction pour couvrir les frais de la plateforme.
            </p>
            <h3>5.3 Paiement</h3>
            <p>
              Le paiement s'effectue en ligne par carte bancaire via la plateforme sécurisée Stripe. 
              Le montant est débité au moment de la réservation.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>6. Politique d'annulation</h2>
            <h3>6.1 Annulation par le client</h3>
            <ul>
              <li><strong>Plus de 48h avant le cours :</strong> Remboursement intégral</li>
              <li><strong>Entre 24h et 48h :</strong> Remboursement de 50%</li>
              <li><strong>Moins de 24h :</strong> Aucun remboursement</li>
            </ul>
            <h3>6.2 Annulation par le moniteur</h3>
            <p>
              En cas d'annulation par le moniteur, le client est intégralement remboursé.
            </p>
            <h3>6.3 Conditions météorologiques</h3>
            <p>
              En cas de fermeture des pistes pour raisons météorologiques ou de sécurité, 
              le cours peut être reporté ou remboursé intégralement.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>7. Droit de rétractation</h2>
            <p>
              Conformément à l'article L221-28 du Code de la consommation, le droit de rétractation 
              ne s'applique pas aux prestations de services de loisirs devant être fournis à une 
              date déterminée. Toutefois, notre politique d'annulation (article 6) permet une 
              flexibilité pour les clients.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>8. Responsabilité</h2>
            <h3>8.1 Responsabilité de SkiMonitor</h3>
            <p>
              SkiMonitor est un intermédiaire technique. La plateforme ne peut être tenue responsable :
            </p>
            <ul>
              <li>De la qualité des cours dispensés par les moniteurs</li>
              <li>Des accidents survenant pendant les cours</li>
              <li>Du non-respect par les utilisateurs de leurs obligations</li>
            </ul>
            <h3>8.2 Responsabilité des moniteurs</h3>
            <p>
              Les moniteurs sont responsables de leurs prestations et doivent disposer d'une 
              assurance responsabilité civile professionnelle couvrant leur activité.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>9. Propriété intellectuelle</h2>
            <p>
              Tous les éléments de la plateforme sont protégés par le droit de la propriété 
              intellectuelle. Toute reproduction non autorisée est interdite.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>10. Modification des CGU</h2>
            <p>
              SkiMonitor se réserve le droit de modifier les présentes CGU à tout moment. 
              Les utilisateurs seront informés des modifications par email ou notification 
              sur la plateforme.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>11. Droit applicable et juridiction</h2>
            <p>
              Les présentes CGU sont soumises au droit français. Tout litige sera soumis 
              aux tribunaux compétents du ressort du siège social de SkiMonitor.
            </p>
          </section>

          <p className="legal-update">Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}</p>
        </CardContent>
      </Card>
    </div>
  );
};

// Politique de Confidentialité (RGPD)
export const PolitiqueConfidentialite = () => {
  return (
    <div className="page-container legal-page" data-testid="politique-confidentialite">
      <div className="page-header">
        <h1>Politique de Confidentialité</h1>
        <p>Protection de vos données personnelles (RGPD)</p>
      </div>

      <Card className="legal-card">
        <CardContent>
          <section>
            <h2>1. Responsable du traitement</h2>
            <p>
              Le responsable du traitement des données personnelles est :<br />
              <strong>[Nom de la société]</strong><br />
              [Adresse]<br />
              Email : [À compléter]
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>2. Données collectées</h2>
            <p>Nous collectons les données suivantes :</p>
            <h3>2.1 Données d'identification</h3>
            <ul>
              <li>Nom et prénom</li>
              <li>Adresse email</li>
              <li>Photo de profil (via Google)</li>
            </ul>
            <h3>2.2 Données professionnelles (moniteurs)</h3>
            <ul>
              <li>Biographie professionnelle</li>
              <li>Spécialités et niveaux enseignés</li>
              <li>Station de rattachement</li>
              <li>Tarif horaire</li>
            </ul>
            <h3>2.3 Données de transaction</h3>
            <ul>
              <li>Historique des réservations</li>
              <li>Montants des transactions (les données bancaires sont traitées par Stripe)</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>3. Finalités du traitement</h2>
            <p>Vos données sont collectées pour :</p>
            <ul>
              <li>Gérer votre compte utilisateur</li>
              <li>Permettre la mise en relation entre clients et moniteurs</li>
              <li>Traiter les réservations et paiements</li>
              <li>Envoyer des notifications relatives aux réservations</li>
              <li>Améliorer nos services</li>
              <li>Respecter nos obligations légales</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>4. Base légale du traitement</h2>
            <p>Le traitement de vos données repose sur :</p>
            <ul>
              <li><strong>L'exécution du contrat :</strong> pour la gestion des réservations</li>
              <li><strong>Le consentement :</strong> pour l'envoi de communications marketing (si applicable)</li>
              <li><strong>L'obligation légale :</strong> pour les obligations comptables et fiscales</li>
              <li><strong>L'intérêt légitime :</strong> pour l'amélioration de nos services</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>5. Destinataires des données</h2>
            <p>Vos données peuvent être partagées avec :</p>
            <ul>
              <li><strong>Les autres utilisateurs :</strong> informations de profil visibles (nom, photo pour les moniteurs)</li>
              <li><strong>Stripe :</strong> pour le traitement des paiements</li>
              <li><strong>Google :</strong> pour l'authentification</li>
              <li><strong>Nos sous-traitants techniques :</strong> hébergement, maintenance</li>
              <li><strong>Les autorités compétentes :</strong> si requis par la loi</li>
            </ul>
            <p>Nous ne vendons jamais vos données personnelles à des tiers.</p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>6. Durée de conservation</h2>
            <ul>
              <li><strong>Données de compte :</strong> conservées pendant la durée de votre inscription + 3 ans</li>
              <li><strong>Données de transaction :</strong> 10 ans (obligation comptable)</li>
              <li><strong>Logs de connexion :</strong> 1 an</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>7. Vos droits</h2>
            <p>Conformément au RGPD, vous disposez des droits suivants :</p>
            <ul>
              <li><strong>Droit d'accès :</strong> obtenir une copie de vos données</li>
              <li><strong>Droit de rectification :</strong> corriger vos données inexactes</li>
              <li><strong>Droit à l'effacement :</strong> demander la suppression de vos données</li>
              <li><strong>Droit à la limitation :</strong> limiter le traitement de vos données</li>
              <li><strong>Droit à la portabilité :</strong> recevoir vos données dans un format structuré</li>
              <li><strong>Droit d'opposition :</strong> vous opposer au traitement de vos données</li>
            </ul>
            <p>
              Pour exercer ces droits, contactez-nous à : <strong>[Email DPO/Contact]</strong>
            </p>
            <p>
              Vous pouvez également introduire une réclamation auprès de la CNIL : 
              <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer"> www.cnil.fr</a>
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>8. Sécurité des données</h2>
            <p>
              Nous mettons en œuvre des mesures techniques et organisationnelles appropriées 
              pour protéger vos données :
            </p>
            <ul>
              <li>Chiffrement des données en transit (HTTPS)</li>
              <li>Authentification sécurisée via OAuth</li>
              <li>Accès restreint aux données personnelles</li>
              <li>Paiements sécurisés via Stripe (certifié PCI-DSS)</li>
            </ul>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>9. Transferts hors UE</h2>
            <p>
              Certaines données peuvent être transférées vers des pays hors de l'Union Européenne 
              (notamment vers les États-Unis pour les services Google et Stripe). Ces transferts 
              sont encadrés par des garanties appropriées (clauses contractuelles types, 
              certifications).
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>10. Cookies</h2>
            <p>
              Notre site utilise uniquement des cookies essentiels au fonctionnement 
              (authentification, session). Aucun cookie publicitaire n'est utilisé.
            </p>
          </section>

          <Separator className="my-6" />

          <section>
            <h2>11. Modification de la politique</h2>
            <p>
              Nous pouvons modifier cette politique de confidentialité. En cas de modification 
              substantielle, nous vous en informerons par email ou notification sur la plateforme.
            </p>
          </section>

          <p className="legal-update">Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}</p>
        </CardContent>
      </Card>
    </div>
  );
};

// Export all
export default { MentionsLegales, CGU, PolitiqueConfidentialite };
