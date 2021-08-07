import os # to remove files
from PIL import Image # Gestion d'image
import csv
from time import perf_counter 
from img_retreiver import retrieve_img_from_CSV # used after conversion in csv
from argparse import ArgumentParser # if launched in main
from tkinter.filedialog import askopenfilename, asksaveasfilename

__VERSION__ = '1.0'

def compress_image(path_to_file: str, quality_factor: int, save_path="", pixel_per_motif=1, keep_csv=0) -> None:
    """
    Compress the image at path_to_file with the given quality_factor at the colors, then saves it to save path
    Will also save motifs.csv and convert.csv if keep_csv_files is True (False by default)

    PARAMETERS :
        - path_to_file : str
            - path of the original image (most format are supported, refer to the pillow docs for more infos)
        - quality_factor : int
            - number which will be used to divide the color bands, as such, must be chosen between 256 and 1 (included)
            - 8 is recommended for best results and speed
            - higher is faster and lighter but less precise, lower is slower and heavier but better quality
        - save_path : str
            - by default (when = ""), will be {orginal_img_path}-compressed.{orignial_img_extension}
            - if set by the user, the path doesn't have to be in the current working directory
        - pixel_per_motif: int
            - used when converting to csv, higher means a lighter convert.csv file, but slower conversion
            - 1 is recommended for best speed (it is the default)
        - keep_csv_files: int (| bool)
            - if true, the motifs and csv conversion of the images will be kept in the working directory after the compression
            - then, the files can be used with img_retriever.py
    """
    assert path_to_file, "the path to the orginal image is empty"
    assert 1 <= quality_factor <= 256, "quality factor is invalid : must be contained in [1;256]"
    if not save_path:
        save_path = path_to_file.split('.')[0]+'-compressed.'+path_to_file.split('.')[1]

    print(f'{(255//quality_factor)**3} couleurs')

    def create_colors(colors_used: list[tuple[int, int, int]], ecart_colors: int) -> list[tuple[int, int, int]]:
        """
        Renvoie les couleurs utiles pour l'image avec l'écart souhaité (qualité souhaitée)

        """
        band_list = [i for i in range(256) if not i % ecart_colors]
        if 255 not in band_list:
            band_list.append(255)
        
        colors = [
            tuple([
                sorted(band_list, key=lambda b: abs(band - b))[0]
                for band in color
            ])
            for color in colors_used
        ]

        return list(set(colors))

    def create_motifs(colors: list[tuple[int, int, int]], n_pixels: int) -> list[tuple[tuple[int, int, int]]]:
        """
        create all possible motifs from the colors, with the pixel per motifs according to pixel_per_motif

        PARAMETERS :
            - colors : list[tuple[int, int, int]]
                - list of all the colors used to create the motifs
            - n_pixels : int
                - equal to pixel_per_motif by default, doesn't need to be motified in normal conditions
        
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
        data = []
        for c in colors:
            ColorToKeep = 1
            for band, b in zip(color, c):
                if abs(band - b) > ecart_colors*.6:
                    ColorToKeep = 0
                    break
            if ColorToKeep: 
                data.append(c)
        for item in data:
            if sum(abs(band - b) for band, b in zip(color, item))/3 <= ecart_colors:
                return item

    img = Image.open(path_to_file)
    img = img.convert('RGB')
    (xImg, yImg) = img.size
    print(f"Taille image : {xImg}x{yImg}")

    print("Simplifying the image...")
    start = perf_counter()
    print("\tCleaning the color list...")
    colors_used = list(set([e[1] for e in img.getcolors(2**24)]))
    colors_used = create_colors(colors_used, quality_factor)
    print("\t..Done")
    dict_nearest_colors = {} # contains all results from get_nearest_color() et optimise image creation when pixels have the same color
    simplifiedImage = [[] for _ in range(yImg)]
    for y in range(yImg):
        for x in range(xImg//pixel_per_motif):
            tmp_list = []
            for i in range(pixel_per_motif):
                pixel = img.getpixel((x*pixel_per_motif+i, y))
                if pixel in dict_nearest_colors.keys(): # there is already a result
                    tmp_list.append(dict_nearest_colors[pixel])
                else: # first time seeing this color
                    nearest_pixel_color = get_nearest_color(pixel, colors_used, quality_factor)
                    dict_nearest_colors[pixel] = nearest_pixel_color
                    tmp_list.append(nearest_pixel_color)
            simplifiedImage[y].append(tuple(tmp_list))

    end = perf_counter()
    execution_time = round((end - start),3)
    print(f'{execution_time}s')
    print("Converting the image...")
    start = perf_counter()
    print("\tCleaning the motif list...")
    motifs = create_motifs(colors_used, pixel_per_motif)    
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
    retrieve_img_from_CSV('convert.csv', save_path)
    end = perf_counter()
    execution_time = round((end - start),3)
    print(f'{execution_time}s')

    if not keep_csv:
        os.remove('convert.csv')
        os.remove('motifs.csv')

def main():
    parser = ArgumentParser(description="Compress images by simplifying the color bands")
    parser.add_argument("path_to_file", type=str, 
                    help="path to the orginal image (put . to choose it with a GUI)")
    parser.add_argument("quality_factor", type=int, 
                    help="factor (value) which will be used to divide the color bands, as such, must be chosen between 256 and 1 (included)")
    parser.add_argument("--save_path", '-s', action='store', type=str, default='',
                    help="path for the compressed image (put . to choose it with a GUI)") 
    parser.add_argument("--pixel_per_motif", '-p', action='store', type=int, default=1,
                    help="number of pixels per motif : if not set, will default at 1 (recommended)")                
    parser.add_argument('--keep_csv', '-c', action='store_true', default=False,
                   help="if set, the csv conversion files will be kept in the working directory")
    parser.add_argument('--version', '-v', action='version', version=f'Image compressor v{__VERSION__}, by Raphaël')
    kwargs = vars(parser.parse_args())
    if kwargs['path_to_file'] == '.':
        kwargs['path_to_file'] = askopenfilename(initialdir=os.getcwd(), title="Image to compress...")
    if kwargs['save_path'] == '.':
        kwargs['save_path'] = asksaveasfilename(initialdir=kwargs['path_to_file'],
            title="Save compressed image...", defaultextension='.'+kwargs['path_to_file'].split('.')[-1], 
                filetypes=(("original img format", "*."+kwargs['path_to_file'].split('.')[-1]), ("other format", "*.*")))
    compress_image(**kwargs)

if __name__=='__main__':
    main()