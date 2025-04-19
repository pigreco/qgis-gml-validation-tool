#!/bin/bash

# Nome del file di input
INPUT_FILE="ple_files_validazione.csv"

# Nome del file di output
OUTPUT_FILE="riepilogo_regioni.csv"

# Verifica se il file di input esiste
if [ ! -f "$INPUT_FILE" ]; then
    echo "Errore: Il file $INPUT_FILE non esiste."
    exit 1
fi

# Genera l'intestazione del file di output
echo "Regione,Totale Files,Files Validi,Files Invalidi,Totale Feature,Feature Invalide" > "$OUTPUT_FILE"

# Estrae l'elenco delle regioni uniche
REGIONI=$(tail -n +2 "$INPUT_FILE" | cut -d, -f1 | sort | uniq)

# Per ogni regione, calcola i totali
for REGIONE in $REGIONI; do
    # Conta il numero totale di file
    TOTALE_FILES=$(grep "^$REGIONE," "$INPUT_FILE" | wc -l)
    
    # Conta i file validi
    FILES_VALIDI=$(grep "^$REGIONE," "$INPUT_FILE" | grep ",Valido," | wc -l)
    
    # Calcola i file invalidi
    FILES_INVALIDI=$((TOTALE_FILES - FILES_VALIDI))
    
    # Somma il totale delle feature
    TOTALE_FEATURE=$(grep "^$REGIONE," "$INPUT_FILE" | cut -d, -f4 | awk '{sum += $1} END {print sum}')
    
    # Somma le feature invalide
    FEATURE_INVALIDE=$(grep "^$REGIONE," "$INPUT_FILE" | cut -d, -f5 | awk '{sum += $1} END {print sum}')
    
    # Aggiungi la riga al file di output
    echo "$REGIONE,$TOTALE_FILES,$FILES_VALIDI,$FILES_INVALIDI,$TOTALE_FEATURE,$FEATURE_INVALIDE" >> "$OUTPUT_FILE"
done

echo "Riepilogo generato in $OUTPUT_FILE"

# Mostra il riepilogo
echo -e "\nRiepilogo per regione:"
column -t -s, "$OUTPUT_FILE"