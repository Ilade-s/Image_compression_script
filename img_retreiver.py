from PIL import Image # Gestion d'image
import csv

def retrieve_img_from_CSV(PathToCsv: str, SavePath: str, motifsPath='motifs.csv'):
    """
    Transform the csv at PathToCsv in a image, using the motifs from the file at motifsPath, then save it to SavePath

    PARAMETERS :
        - PathToCsv : str
            - path to the csv file representing the compressed image, obtained with img_compressor.py
        - SavePath : str
            - path which will be used to save the recreated/compressed image
        - motifsPath : str
            - motifs.csv by default, must be the same file used at creation in img_compressor.py
    """    
    with open(PathToCsv, 'r', newline='\n') as file:
        reader = csv.reader(file)
        img_matrice = []
        for line in reader:
            current_line = []
            n_motifs_line = 0
            for e in line:
                if len(e.split('-')) == 2:
                    (i_motif, n_motifs) = e.split('-')
                    n_motifs = int(n_motifs, 16)
                else:
                    i_motif = e
                    n_motifs = 1
                n_motifs_line += n_motifs
                for _ in range(n_motifs):
                    current_line.append(int(i_motif, 16))
            img_matrice.append(current_line)

    with open(motifsPath, 'r', newline='\n') as file:
        reader = csv.reader(file)
        hexMotifs = [*reader]
        motifs = [
            tuple([
                (
                int(hexa[:2], 16),
                int(hexa[2:4], 16),
                int(hexa[4:], 16),
                )
                for hexa in motif
            ])   
            for motif in hexMotifs
        ]
        img_data_matrice = [[] for _ in range(len(img_matrice))]
        current_line = 0
        for line in img_matrice:
            for nMotif in line:
                img_data_matrice[current_line].extend([*motifs[nMotif]])
            current_line += 1

    img = Image.new('RGB', (len(img_data_matrice[0]), len(img_data_matrice)))

    for line in range(len(img_data_matrice)):
        for col in range(len(img_data_matrice[0])):
            img.putpixel((col, line), img_data_matrice[line][col])

    img.save(SavePath)

if __name__=='__main__':
    # Paths to files/save (change them if necessary)
    SavePath = "images/save.png"
    PathToCsv = 'convert.csv'
    print("Retreiving the compressed image...")
    retrieve_img_from_CSV(PathToCsv, SavePath)