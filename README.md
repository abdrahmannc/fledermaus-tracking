# fledermaus-tracking
# Digitale Fledermauserfassung und -verfolgung

## Projektbeschreibung

Dieses Projekt wurde im Rahmen eines **Kooperationsprojekts zwischen der Technischen Hochschule Ostwestfalen-Lippe (TH OWL), Standort Höxter, und der IfAÖ GmbH, Rostock** durchgeführt. Ziel des Projekts ist die **automatische Erkennung und Nachverfolgung von Fledermäusen** in Wärmebild- oder Infrarot-Videodaten. Dabei wird **klassische Bildverarbeitung mit OpenCV** verwendet, ohne den Einsatz von künstlicher Intelligenz, um die Fledermäuse zu erkennen und ihre Flugbahnen zu verfolgen.

Das Hauptziel ist die Unterstützung bei der Identifikation von **potenziellen Quartieren** (z. B. an Gebäudefassaden), um die rechtlichen Anforderungen bei geplanten Bauvorhaben oder Rodungsmaßnahmen zu erfüllen. Die Ergebnisse werden in benutzerfreundlichen Formaten wie CSV oder JSON exportiert, um die Analyse und Validierung der Daten zu erleichtern.

## Funktionen

- **Erkennung von Fledermäusen**: Identifikation von Fledermäusen in Thermal- und IR-Videodaten.
- **Verfolgung und Tracking**: Verfolgung der Fledermäuse im Video zur Analyse von Flugrouten.
- **Datenexport**: Export der Ergebnisse als CSV oder JSON.
- **Benutzeroberfläche**: Einfach zu bedienende Oberfläche, die es auch ohne tiefgehende technische Kenntnisse ermöglicht, die Ergebnisse zu analysieren.

## Technologien

- **Frontend**: React (ursprünglich HTML, CSS, JavaScript)
- **Backend**: Python (FastAPI)
- **Videoanalyse**: OpenCV

### ⚠️ Hinweis
Dieses Projekt wurde ursprünglich mit einfachem HTML, CSS und JavaScript gestartet. Aufgrund zunehmender Komplexität wurde der Code auf **React** migriert, um Struktur, Wiederverwendbarkeit und Wartbarkeit zu verbessern. Frühere Versionen findest du im Git-Verlauf.

## Installation

### 1. Klonen Sie das Repository

```bash
git clone https://github.com/Abderrahmanec/fledermaus-tracking.git
cd fledermaus-tracking
