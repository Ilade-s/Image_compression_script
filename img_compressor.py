from PIL import Image # Gestion d'image
import csv
from time import perf_counter
from img_retreiver import retrieve_img_from_CSV

# Variables used in the program, can be changed, paths must be safe filenames
PATH_TO_FILE = 'images/Lazy_club.png' # path of the original image
SAVE_PATH = PATH_TO_FILE.split('.')[0]+'-compressed.'+PATH_TO_FILE.split('.')[1] # path to save the compressed image
PIXEL_PER_MOTIF = 1 # possible choices in [1, 2, 3] (1 is very much recommended)
ECART_COLORS = 64 # 1 means all the [0;255] band will be used, if more the band will be divided by the given number
print(f'{(255//ECART_COLORS)**3} couleurs')

def create_colors(colors_used: list[tuple[int, int, int]], ecart_colors: int) -> list[tuple[int, int, int]]:
    """
    Renvoie les couleurs utiles pour l'image avec l'écart souhaité (qualité souhaitée)

    """
    band_list = [i for i in range(256) if not i % ecart_colors] + [255]
    
    colors = [
        tuple([
            sorted(band_list, key=lambda b: abs(band - b))[0]
            for band in color
        ])
        for color in colors_used
    ]

    return list(set(colors))

def create_motifs(colors: list[tuple[int, int, int]], n_pixels=PIXEL_PER_MOTIF) -> list[tuple[tuple[int, int, int]]]:
    """
    create all possible motifs from the colors, with the pixel per motifs according to PIXEL_PER_MOTIF

    PARAMETERS :
        - colors : list[tuple[int, int, int]]
            - list of all the colors used to create the motifs
        - n_pixels : int
            - equal to PIXEL_PER_MOTIF by default, doesn't need to be motified in normal conditions
    
    RETURN :
        - motifs : list[tuple[tuple[int, int, int]]]
            - list of all the motifs possible with the given colors in {n_pixels}-tuple
    """
    motifs = []
    if n_pixels == 1:
        for c1 in colors:
            motifs.append((c1,)) 

    elif n_pixels == 2:
        for c1 in colors:
            for c2 in colors:  
                motifs.append((c1, c2)) 

    elif n_pixels == 3:
        for c1 in colors:
            for c2 in colors:  
                for c3 in colors:
                    motifs.append((c1, c2, c3)) 

    return motifs   

def save_motifs(motifs: list[tuple[tuple[int, int, int]]]) -> None:
    """
    Saves the motifs in hexadecimal
    """
    hexMotifs = [
        [
            ''.join([hex(band)[2:].zfill(2) for band in color])
            for color in motif
        ]
        for motif in motifs
    ]

    with open("motifs.csv", "w+", newline='\n') as file:
        w = csv.writer(file)
        w.writerows(hexMotifs)

def get_nearest_color(color: tuple[int, int, int], colors: list[tuple[int, int, int]], ecart_colors: int) -> tuple[int, int, int]:
    """
    Donne la couleur simplifiée la plus proche de la couleur donnée

    PARAMETRES :
        - color : tuple[int, int, int]
            - couleur à simplifier
        - data : list[tuple[int, int, int]]
            - liste des couleurs simplifiées

    SORTIE :
        - color : tuple[int, int, int]
            - couleur identifiée
    """
    data = [*colors]
    for c in colors:
        ColorToRemove = 0
        for band, b in zip(color, c):
            if abs(band - b) > ecart_colors*.6:
                ColorToRemove = 1
        if ColorToRemove: data.remove(c)
    for item in data:
        if sum(abs(band - b) for band, b in zip(color, item))/3 <= ecart_colors:
            return item

img = Image.open(PATH_TO_FILE)
img = img.convert('RGB')
(xImg, yImg) = img.size
print(f"Taille image : {xImg}x{yImg}")

print("Simplifying the image...")
start = perf_counter()
print("\tCleaning the color list...")
colors_used = list(set([e[1] for e in img.getcolors(2**24)]))
colors_used = create_colors(colors_used, ECART_COLORS)
print("\t..Done")
dict_nearest_colors = {} # contains all results from get_nearest_color() et optimise image creation when pixels have the same color
simplifiedImage = [[] for _ in range(yImg)]
for y in range(yImg):
    for x in range(xImg//PIXEL_PER_MOTIF):
        for i in range(PIXEL_PER_MOTIF):
            tmp_list = []
            pixel = img.getpixel((x*PIXEL_PER_MOTIF+i, y))
            if pixel in dict_nearest_colors.keys(): # there is already a result
                tmp_list.append(dict_nearest_colors[pixel])
            else: # first time seeing this color
                nearest_pixel_color = get_nearest_color(pixel, colors_used, ECART_COLORS)
                dict_nearest_colors[pixel] = nearest_pixel_color
                tmp_list.append(nearest_pixel_color)
        simplifiedImage[y].append(tuple(tmp_list))

end = perf_counter()
execution_time = round((end - start),3)
print(f'{execution_time}s')

print("Converting the image...")
start = perf_counter()
print("\tCleaning the motif list...")
motifs = create_motifs(colors_used)
save_motifs(motifs)
print("\t...Done")

convertedImage = []
for line in simplifiedImage:
    current_line = []
    n_same_motif = 1
    past_motif = ()
    iter_line = iter(line)
    next_motif = next(iter_line)
    for motif in line:
        next_motif = next(iter_line, ())
        if motif == past_motif:
            n_same_motif += 1
            if motif != next_motif:
                if n_same_motif > 1:
                    current_line.append(f'{hex(motifs.index(motif))[2:]}-{hex(n_same_motif)[2:]}')
                else:
                    current_line.append(hex(motifs.index(motif))[2:])
                n_same_motif = 1
        else:
            if motif != next_motif:
                if n_same_motif > 1:
                    current_line.append(f'{hex(motifs.index(motif))[2:]}-{hex(n_same_motif)[2:]}')
                else:
                    current_line.append(hex(motifs.index(motif))[2:])
            n_same_motif = 1
        past_motif = motif
    convertedImage.append(current_line)


end = perf_counter()
execution_time = round((end - start),3)
print(f'{execution_time}s')

with open('convert.csv', "w+", newline='\n') as convertFile:
    w = csv.writer(convertFile)
    w.writerows(convertedImage)
    
# réécriture
print("Retreiving the compressed image...")
start = perf_counter()
retrieve_img_from_CSV('convert.csv', SAVE_PATH)
end = perf_counter()
execution_time = round((end - start),3)
print(f'{execution_time}s')