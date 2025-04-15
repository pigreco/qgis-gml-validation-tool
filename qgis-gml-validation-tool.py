import os
from qgis.core import QgsVectorLayer, QgsGeometry
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.utils import iface

# Chiedi all'utente di selezionare la cartella contenente i file GML
cartella_gml = QFileDialog.getExistingDirectory(iface.mainWindow(), "Seleziona la cartella contenente i file GML")

# Verifica se l'utente ha annullato la selezione
if not cartella_gml:
    print("Operazione annullata.")
    exit()

# Ottieni il nome della cartella di input (per usarlo nel nome dei file di output)
nome_cartella = os.path.basename(cartella_gml)
if not nome_cartella:  # Nel caso di percorso radice
    nome_cartella = "gml_validazione"

# Inizializza un dizionario per raccogliere i risultati
risultati = {}

# Conta i file GML trovati
num_gml_files = len([f for f in os.listdir(cartella_gml) if f.lower().endswith('.gml')])
if num_gml_files == 0:
    print(f"Nessun file GML trovato nella cartella: {cartella_gml}")
    exit()
else:
    print(f"Trovati {num_gml_files} file GML nella cartella: {cartella_gml}")
    print("Inizio della validazione...")

# Elabora tutti i file GML nella cartella
for idx, file_name in enumerate(os.listdir(cartella_gml)):
    if file_name.lower().endswith('.gml'):
        print(f"Elaborazione {idx+1}/{num_gml_files}: {file_name}")
        file_path = os.path.join(cartella_gml, file_name)
        
        # Carica il layer GML
        layer = QgsVectorLayer(file_path, file_name, "ogr")
        
        # Controlla se il layer è stato caricato correttamente
        if not layer.isValid():
            risultati[file_name] = {"stato": "Errore di caricamento", "dettagli": "Impossibile caricare il layer"}
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
            risultati[file_name] = {
                "stato": "Contiene geometrie invalide", 
                "numero_invalide": len(feature_invalide),
                "totale_feature": total_features,
                "dettagli": feature_invalide
            }
        else:
            risultati[file_name] = {
                "stato": "Valido", 
                "numero_invalide": 0,
                "totale_feature": total_features
            }

# Stampa un riepilogo dei risultati
print("\nRisultati della validazione dei file GML:")
print("----------------------------------------")
for file_name, info in risultati.items():
    print(f"File: {file_name}")
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

# Chiedi all'utente se vuole salvare i risultati in un file CSV
if risultati:
    reply = QMessageBox.question(iface.mainWindow(), 'Salvare i risultati?',
                                'Vuoi salvare i risultati della validazione in un file CSV?',
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    
    if reply == QMessageBox.Yes:
        # Genera automaticamente i nomi dei file basati sul nome della cartella
        output_file = os.path.join(cartella_gml, f"{nome_cartella}_validazione.csv")
        output_detail_file = os.path.join(cartella_gml, f"{nome_cartella}_validazione_dettagli.csv")
        
        # Chiedi all'utente dove salvare il file riepilogativo
        output_file, _ = QFileDialog.getSaveFileName(iface.mainWindow(), "Salva risultati come CSV", 
                                                   output_file,
                                                   "File CSV (*.csv)")
        
        if output_file:
            # Adatta il percorso dei dettagli in base alla scelta dell'utente
            output_dir = os.path.dirname(output_file)
            output_basename = os.path.basename(output_file)
            output_basename_noext = os.path.splitext(output_basename)[0]
            output_detail_file = os.path.join(output_dir, f"{output_basename_noext}_dettagli.csv")
            
            import csv
            
            # File CSV principale con riepilogo
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['File', 'Stato', 'Totale feature', 'Feature invalide'])
                
                for file_name, info in risultati.items():
                    writer.writerow([
                        file_name, 
                        info['stato'], 
                        info.get('totale_feature', 'N/A'), 
                        info.get('numero_invalide', 'N/A')
                    ])
            
            # File CSV dettagliato con tutti gli errori
            with open(output_detail_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['File', 'Feature ID', 'Messaggio di errore'])
                
                for file_name, info in risultati.items():
                    if 'dettagli' in info and info['dettagli']:
                        for errore in info['dettagli']:
                            writer.writerow([
                                file_name,
                                errore['id'],
                                errore['errore']
                            ])
            
            print(f"Risultati salvati in: {output_file}")
            print(f"Dettagli completi degli errori salvati in: {output_detail_file}")
        else:
            print("Salvataggio CSV annullato.")

print("Validazione completata!")
