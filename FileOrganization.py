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
        if type_path == 'data/output/New_Cycle_Data.csv':
            continue
        else:
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
                cell_eis_path = Data_Repository + 'eis/' + cell_number
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
                elif extension == '.xlsx':
                    if os.path.exists(cell_csv_path):
                        shutil.move(file_path, cell_eis_path)
                    else:
                        os.mkdir(cell_eis_path)
                        shutil.move(file_path, cell_eis_path)

def Organize_eis(Repository):
    eis_folder = Repository + 'eis/'
    eis_files = os.listdir(eis_folder)
    for file in eis_files:
        eis_path = os.path.join(eis_folder, file)
        if os.path.isdir(eis_path):
            pass
        else:
            cell_number = file.split('_')[0]
            cell_eis_path = eis_folder + cell_number
            if os.path.exists(cell_eis_path):
                if os.path.exists(cell_eis_path + '/' + file):
                    os.remove(eis_path)
                else:
                    shutil.move(eis_path, cell_eis_path)
            else:
                os.mkdir(cell_eis_path)
                shutil.move(eis_path, cell_eis_path)


MoveFiles(Directory, Repository)
Organize_eis(Repository)
