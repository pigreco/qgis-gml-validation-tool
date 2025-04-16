"""
QGIS GML Validation Tool
------------------------
Questo script è un'utility per QGIS che consente di validare file GML (Geography Markup Language).
Lo strumento verifica la validità delle geometrie contenute nei file GML e genera report
dettagliati dei problemi riscontrati.

Funzionalità principali:
- Scansione ricorsiva di una cartella contenente file GML
- Validazione delle geometrie di ciascun file utilizzando la libreria GEOS
- Generazione di un riepilogo della validazione
- Esportazione dei risultati in formato CSV

Tecnologie utilizzate:
- GEOS (Geometry Engine Open Source): utilizzato attraverso QGIS per la validazione
  delle geometrie spaziali, verifica la conformità con gli standard OGC (Open Geospatial Consortium)
- GML (Geography Markup Language): formato standard OGC basato su XML per la rappresentazione
  di informazioni geografiche

Librerie utilizzate:
- os: per operazioni sul filesystem
- qgis.core: per accedere alle funzionalità di QGIS (QgsVectorLayer, QgsGeometry)
- qgis.PyQt.QtWidgets: per interfaccia utente (QFileDialog, QMessageBox, QDialog, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QDialogButtonBox, QCheckBox)
- qgis.utils: per interagire con l'interfaccia di QGIS (iface)
- csv: per l'esportazione dei risultati in formato CSV
"""

import os
import csv
from qgis.core import QgsVectorLayer, QgsGeometry
from qgis.PyQt.QtWidgets import (QFileDialog, QMessageBox, QDialog, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QDialogButtonBox, QCheckBox)
from qgis.utils import iface

class GmlValidationDialog(QDialog):
    def __init__(self, parent=None):
        super(GmlValidationDialog, self).__init__(parent)
        self.setWindowTitle("Validazione GML")
        self.resize(500, 180)
        
        # Creo il layout principale
        layout = QVBoxLayout()
        
        # Sezione cartella input
        input_layout = QHBoxLayout()
        input_label = QLabel("Cartella GML:")
        self.input_path = QLineEdit()
        input_button = QPushButton("Sfoglia...")
        input_button.clicked.connect(self.sfoglia_input)
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_button)
        
        # Sezione cartella output
        output_layout = QHBoxLayout()
        output_label = QLabel("Cartella output:")
        self.output_path = QLineEdit()
        output_button = QPushButton("Sfoglia...")
        output_button.clicked.connect(self.sfoglia_output)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        
        # Checkbox per la ricerca ricorsiva
        self.recursive_checkbox = QCheckBox("Cerca ricorsivamente nelle sottocartelle")
        self.recursive_checkbox.setChecked(True)  # Selezionato di default
        
        # Pulsanti standard (OK e Annulla)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Assemblo il layout
        layout.addLayout(input_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.recursive_checkbox)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def sfoglia_input(self):
        cartella = QFileDialog.getExistingDirectory(self, "Seleziona la cartella contenente i file GML")
        if cartella:
            self.input_path.setText(cartella)
    
    def sfoglia_output(self):
        cartella = QFileDialog.getExistingDirectory(self, "Seleziona la cartella per i file di output")
        if cartella:
            self.output_path.setText(cartella)

def trova_file_gml_ricorsivamente(cartella_base, ricorsivo=True):
    """
    Trova tutti i file GML in una cartella e opzionalmente nelle sue sottocartelle.
    
    Args:
        cartella_base (str): Percorso della cartella da cui iniziare la ricerca
        ricorsivo (bool): Se True, cerca anche nelle sottocartelle
        
    Returns:
        list: Lista di percorsi completi dei file GML trovati
    """
    file_gml = []
    
    if ricorsivo:
        # Ricerca ricorsiva
        for root, dirs, files in os.walk(cartella_base):
            for file in files:
                if file.lower().endswith('.gml'):
                    file_gml.append(os.path.join(root, file))
    else:
        # Solo nella cartella principale
        for file in os.listdir(cartella_base):
            if file.lower().endswith('.gml'):
                file_gml.append(os.path.join(cartella_base, file))
    
    return file_gml

def valida_gml():
    # Mostra la finestra di dialogo per selezionare le cartelle
    dialog = GmlValidationDialog(iface.mainWindow())
    result = dialog.exec_()
    
    # Verifica se l'utente ha annullato
    if result != QDialog.Accepted:
        print("Operazione annullata.")
        return
    
    # Ottieni i percorsi dalle caselle di testo
    cartella_gml = dialog.input_path.text()
    cartella_output = dialog.output_path.text()
    ricorsivo = dialog.recursive_checkbox.isChecked()
    
    # Verifica se la cartella GML è stata specificata
    if not cartella_gml:
        QMessageBox.warning(iface.mainWindow(), "Errore", "La cartella GML non è stata specificata.")
        return
    
    # Verifica se la cartella di output è stata specificata
    if not cartella_output:
        cartella_output = cartella_gml  # Usa la stessa cartella di input se non specificata
    
    # Ottieni il nome della cartella di input (per usarlo nel nome dei file di output)
    nome_cartella = os.path.basename(cartella_gml)
    if not nome_cartella:  # Nel caso di percorso radice
        nome_cartella = "gml_validazione"
    
    # Trova tutti i file GML
    file_gml_trovati = trova_file_gml_ricorsivamente(cartella_gml, ricorsivo)
    
    # Verifica se sono stati trovati file GML
    if not file_gml_trovati:
        QMessageBox.warning(iface.mainWindow(), "Avviso", 
                           f"Nessun file GML trovato nella cartella{' e sottocartelle' if ricorsivo else ''}: {cartella_gml}")
        return
    
    # Inizializza un dizionario per raccogliere i risultati
    risultati = {}
    
    print(f"Trovati {len(file_gml_trovati)} file GML nella cartella{' e sottocartelle' if ricorsivo else ''}: {cartella_gml}")
    print("Inizio della validazione...")
    
    # Elabora tutti i file GML trovati
    for idx, file_path in enumerate(file_gml_trovati):
        file_name = os.path.basename(file_path)
        percorso_relativo = os.path.relpath(file_path, cartella_gml)
        
        print(f"Elaborazione {idx+1}/{len(file_gml_trovati)}: {percorso_relativo}")
        
        # Carica il layer GML
        layer = QgsVectorLayer(file_path, file_name, "ogr")
        
        # Controlla se il layer è stato caricato correttamente
        if not layer.isValid():
            risultati[percorso_relativo] = {"stato": "Errore di caricamento", "dettagli": "Impossibile caricare il layer"}
            continue
        
        # Controlla la validità di ogni geometria nel layer
        feature_invalide = []
        total_features = layer.featureCount()
        
        # Mostra un feedback di progresso
        if total_features > 100:
            print(f"  Il file contiene {total_features} feature, questo potrebbe richiedere tempo...")
        
        for feature in layer.getFeatures():
            geom = feature.geometry()
            if not geom.isGeosValid():
                feature_invalide.append({
                    'id': feature.id(),
                    'errore': geom.lastError()
                })
        
        # Aggiungi i risultati al dizionario
        if feature_invalide:
            risultati[percorso_relativo] = {
                "stato": "Contiene geometrie invalide", 
                "numero_invalide": len(feature_invalide),
                "totale_feature": total_features,
                "dettagli": feature_invalide
            }
        else:
            risultati[percorso_relativo] = {
                "stato": "Valido", 
                "numero_invalide": 0,
                "totale_feature": total_features
            }

    # Stampa un riepilogo dei risultati
    print("\nRisultati della validazione dei file GML:")
    print("----------------------------------------")
    for file_percorso, info in risultati.items():
        print(f"File: {file_percorso}")
        print(f"Stato: {info['stato']}")
        
        if 'totale_feature' in info:
            print(f"Totale feature: {info['totale_feature']}")
        
        if 'numero_invalide' in info and info['numero_invalide'] > 0:
            print(f"Feature invalide: {info['numero_invalide']}")
            
            # Opzionale: stampa dettagli delle prime 5 feature invalide
            print("Dettagli dei primi errori:")
            for i, feat in enumerate(info['dettagli'][:5]):
                print(f"  - Feature ID: {feat['id']}, Errore: {feat['errore']}")
            
            if len(info['dettagli']) > 5:
                print(f"  ... e altri {len(info['dettagli']) - 5} errori")
        
        print("----------------------------------------")

    # Genera e salva automaticamente i file CSV
    if risultati:
        # Genera i nomi dei file basati sul nome della cartella
        output_file = os.path.join(cartella_output, f"{nome_cartella}_validazione.csv")
        output_detail_file = os.path.join(cartella_output, f"{nome_cartella}_validazione_dettagli.csv")
        
        # File CSV principale con riepilogo
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['File', 'Stato', 'Totale feature', 'Feature invalide'])
            
            for file_percorso, info in risultati.items():
                writer.writerow([
                    file_percorso, 
                    info['stato'], 
                    info.get('totale_feature', 'N/A'), 
                    info.get('numero_invalide', 'N/A')
                ])
        
        # File CSV dettagliato con tutti gli errori
        with open(output_detail_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['File', 'Feature ID', 'Messaggio di errore'])
            
            for file_percorso, info in risultati.items():
                if 'dettagli' in info and info['dettagli']:
                    for errore in info['dettagli']:
                        writer.writerow([
                            file_percorso,
                            errore['id'],
                            errore['errore']
                        ])
        
        print(f"Risultati salvati in: {output_file}")
        print(f"Dettagli completi degli errori salvati in: {output_detail_file}")
        
        # Mostra un messaggio di completamento
        QMessageBox.information(iface.mainWindow(), "Validazione completata",
                               f"La validazione di {len(file_gml_trovati)} file GML è stata completata.\n\n"
                               f"Risultati salvati in:\n- {output_file}\n- {output_detail_file}")
    else:
        print("Nessun risultato da salvare.")

    print("Validazione completata!")

# Esegui lo script quando viene caricato
valida_gml()
