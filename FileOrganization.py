import os
import shutil
from dotenv import load_dotenv

load_dotenv()
Directory = os.getenv('Directory')
Repository = os.getenv('Repository')

def MoveFiles(Directory, Data_Repository):
    output_folder = Directory + 'output/'
    file_types = os.listdir(output_folder)
    for type in file_types:
        type_path = os.path.join(output_folder, type)
        files = os.listdir(type_path)
        for file in files:
            file_path = os.path.join(type_path, file)
            filename, extension = os.path.splitext(file)
            if filename == '.gitkeep':
                continue
            else:
                cell_number = filename.split('_')[1]
                file_type = filename.split('_')[-1]
                cell_csv_path = Data_Repository + 'csv/' + cell_number
                cell_capVplot_path = Data_Repository + 'capVplots/' + cell_number
                cell_dqdvplot_path = Data_Repository + 'dqdvPlots/' + cell_number
                if extension == '.png':
                    if file_type == 'CellCapV':
                        if os.path.exists(cell_capVplot_path):
                            if os.path.exists(cell_capVplot_path + '/' + filename + '.png'):
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, cell_capVplot_path)
                        else:
                            os.mkdir(cell_capVplot_path)
                            shutil.move(file_path, cell_capVplot_path)
                    elif file_type == 'SpecificCapV':
                        if os.path.exists(cell_capVplot_path):
                            if os.path.exists(cell_capVplot_path + '/' + filename + '.png'):
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, cell_capVplot_path)
                        else:
                            os.mkdir(cell_capVplot_path)
                            shutil.move(file_path, cell_capVplot_path)
                    elif file_type == 'dqdv':
                        if os.path.exists(cell_dqdvplot_path):
                            if os.path.exists(cell_dqdvplot_path + '/' + filename + '.png'):
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, cell_dqdvplot_path)
                        else:
                            os.mkdir(cell_dqdvplot_path)
                            shutil.move(file_path, cell_dqdvplot_path)
                elif extension == '.csv':
                    if file_type == 'cycle':
                        if os.path.exists(cell_csv_path):
                            if os.path.exists(cell_csv_path + '/' + filename + '.csv'):
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, cell_csv_path)
                        else:
                            os.mkdir(cell_csv_path)
                            shutil.move(file_path, cell_csv_path)
                    elif file_type == 'dqdv':
                        if os.path.exists(cell_csv_path):
                            if os.path.exists(cell_csv_path + '/' + filename + '.csv'):
                                os.remove(file_path)
                            else:
                                shutil.move(file_path, cell_csv_path)
                        else:
                            os.mkdir(cell_csv_path)
                            shutil.move(file_path, cell_csv_path)
                    else:
                        continue


MoveFiles(Directory, Repository)

