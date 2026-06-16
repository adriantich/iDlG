import asyncio

import pandas as pd
from shiny import render, reactive, ui
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from .server_tools import *
from pathlib import Path

from explorer.loader import VCFLoader
from scanners.scan_by_pos import ScannerByPos
from scanners.scan_by_snps import ScannerBySNP
import json
from .interactive_plot import CreatePlot
import matplotlib.pyplot as plt
import io, base64

def app_server(input, output, session):
    
    reload_project_text = reactive.value(None)
    vcf_object = reactive.value(None)
    temp_folder = reactive.value(None)
    data_loaded_correctly = reactive.value(None)
    analysis_finished_correctly = reactive.value(None)
    scan_by_snps_params = reactive.value(None)
    scan_by_position_params = reactive.value(None)

    params_updated = reactive.value(False)

    chromosomes_global = reactive.value(None)
    window_sizes_global = reactive.value(None)
    step_sizes_global = reactive.value(None)

    @render.ui
    @reactive.event(input.create_plot)
    def scan_plot():
        print("scan_plot running")
        # Generate the plot using the global reactive values
        chromosomes = input.selected_chromosome()
        window = input.selected_window_size()
        step = input.selected_step_size()
        if input.plot_by_snps():
            scanner = "bysnps"
            input_path = os.path.join(temp_folder.get(), "scan_by_snps_results") if temp_folder.get() else Path("scan_by_snps_results")
        elif input.plot_by_position():
            scanner = "bypos"
            input_path = os.path.join(temp_folder.get(), "scan_by_pos_results") if temp_folder.get() else Path("scan_by_pos_results")
        else:
            return ui.div("Please select a scanning method to plot.")
        
        parquet_file = os.path.join(input_path, f"{chromosomes}_{window}_{step}_{scanner}_mean.parquet")

        if not os.path.exists(parquet_file):
            return ui.img(src= os.path.join(os.path.dirname(__file__), "plot_not_avilable_edited.gif"))
        else:
            print(f"Creating plot for chromosome {chromosomes}, window size {window}, step size {step}")
            plot_created = CreatePlot(
                chromosomes=chromosomes,
                window=window,
                step=step,
                parquet_path=parquet_file
            )
            print(f"Plot created: {plot_created.fig}")
            if plot_created.fig is None:
                return ui.div("Error creating plot. Please check the parameters and try again.",
                              ui.img(src= os.path.join(os.path.dirname(__file__), "plot_not_avilable_edited.gif")))
            else:
                buf = io.BytesIO()
                plot_created.fig.savefig(buf, format="png")
                buf.seek(0)
                plt.close(plot_created.fig)

                img_b64 = base64.b64encode(buf.read()).decode("utf-8")
                return ui.HTML(f'<img src="data:image/png;base64,{img_b64}">')
            
    @render.ui
    def selected_chromosome():
        print("selected_chromosome running")
        chromosomes = chromosomes_global.get()
        if input.plot_by_snps() or input.plot_by_position():
            if chromosomes:
                return ui.input_select(
                    "selected_chromosome",
                    "Select chromosome to plot",
                    choices={x: x for x in chromosomes},
                )
        return ui.input_select(
            "selected_chromosome",
            "Select chromosome to plot",
            choices={},
        )


    @render.ui
    def selected_step_size():
        print("selected_step_size running")
        step_sizes = step_sizes_global.get()
        if input.plot_by_snps() or input.plot_by_position():
            if step_sizes:
                return ui.input_select(
                    "selected_step_size",
                    "Select step size to plot",
                    choices={x: x for x in step_sizes},
                )
        return ui.input_select(
            "selected_step_size",
            "Select step size to plot",
            choices={},
        )
    
    @render.ui
    def selected_window_size():
        print("selected_window_size running")
        window_sizes = window_sizes_global.get()
        if input.plot_by_snps() or input.plot_by_position():
            if window_sizes:
                return ui.input_select(
                    "selected_window_size",
                    "Select window size to plot",
                    choices={x: x for x in window_sizes},
                )
        return ui.input_select(
            "selected_window_size",
            "Select window size to plot",
            choices={},
        )

    @reactive.effect
    def _():
        print("reactive to plot_by_snps")
        if input.plot_by_snps():
            session.send_input_message("plot_by_position", {"value": False})
            params = scan_by_snps_params.get()
            print(f"scan_by_snps_params: {params}")
            if params:
                chromosomes = set([x[1] for x in params])
                chromosomes_global.set(chromosomes)
                print(f"chromosomes: {chromosomes}")
                window_sizes = set([int(x[2]) for x in params])
                window_sizes_global.set(window_sizes)
                step_sizes = set([int(x[3]) for x in params])
                step_sizes_global.set(step_sizes)
                # session.send_input_message("selected_chromosome", {"choices": {x: x for x in chromosomes}})
                # session.send_input_message("selected_window_size", {"choices": {x: x for x in window_sizes}})
                # session.send_input_message("selected_step_size", {"choices": {x: x for x in step_sizes}})
            else:
                if params_updated.get():
                    ui.notification_show("No parameters found for scan_by_snps. Please run a scan first.", type="error")
                    return "No parameters found for scan_by_snps. Please run a scan first."

    @reactive.effect
    def _():
        print("reactive to plot_by_position")
        if input.plot_by_position():
            session.send_input_message("plot_by_snps", {"value": False})
            params = scan_by_position_params.get()
            print(f"scan_by_position_params: {params}")
            if params:
                chromosomes = set([x[1] for x in params])
                chromosomes_global.set(chromosomes)
                print(f"chromosomes: {chromosomes}")
                window_sizes = set([int(x[2]) for x in params])
                window_sizes_global.set(window_sizes)
                step_sizes = set([int(x[3]) for x in params])
                step_sizes_global.set(step_sizes)
                # session.send_input_message("selected_chromosome", {"choices": {x: x for x in chromosomes}})
                # session.send_input_message("selected_window_size", {"choices": {x: x for x in window_sizes}})
                # session.send_input_message("selected_step_size", {"choices": {x: x for x in step_sizes}})
            else:
                ui.notification_show("No parameters found for scan_by_position. Please run a scan first.", type="error")
                return "No parameters found for scan_by_position. Please run a scan first."
    

    @reactive.effect
    def _():
        print("params reactive effect running")
        cond1 = vcf_object.get() is not None
        cond2 = data_loaded_correctly.get() is True
        cond3 = analysis_finished_correctly.get() is True
        cond4 = temp_folder.get() is not None
        if cond1 or cond2 or cond3 or cond4:
            print("updating scan parameters from project folder")
            if os.path.exists(os.path.join(temp_folder.get(), "scan_by_snps_results", "scan_params.json")):
                with open(os.path.join(temp_folder.get(), "scan_by_snps_results", "scan_params.json"), "r") as f:
                    params = json.load(f)
                    params = params.get("result_index", None)
                    scan_by_snps_params.set(params)
                    print(f"Updated scan_by_snps_params: {params}")
            if os.path.exists(os.path.join(temp_folder.get(), "scan_by_position_results", "scan_params.json")):
                with open(os.path.join(temp_folder.get(), "scan_by_position_results", "scan_params.json"), "r") as f:
                    params = json.load(f)
                    params = params.get("result_index", None)
                    scan_by_position_params.set(params)
                    print(f"Updated scan_by_position_params: {params}")
            params_updated.set(True)

    @reactive.effect
    def _():
        print("reactive to scan_by_snps")
        if input.scan_by_snps():
            session.send_input_message("scan_by_position", {"value": False})
            session.send_input_message("step_sizes", {"value": "500\n1500\n2500"})
            session.send_input_message("window_sizes", {"value": "500\n1500\n2500"})
    
    @reactive.effect
    def _():
        print("reactive to scan_by_position")
        if input.scan_by_position():
            session.send_input_message("scan_by_snps", {"value": False})
            session.send_input_message("step_sizes", {"value": "1000000\n5000000"})
            session.send_input_message("window_sizes", {"value": "1000000\n5000000"})
    
    @reactive.effect
    def _():
        if temp_folder.get() is not None:
            project_file = os.path.join(temp_folder.get(), "input_data.parquet")
            if os.path.exists(project_file):
                session.send_input_message("use_project_data", {"value": True})
            else:
                session.send_input_message("use_project_data", {"value": False})
    
        
    @reactive.effect
    @reactive.event(input.create_project)
    def load_project():
        print("load_project running")
        file_info = input.project_file()[0] if input.project_file() else None
        file_name = input.project_name()
        print(input.project_file())
        print(input.project_name())
        if file_name:
            print(f"Creating project folder: {file_name}")
            os.makedirs(file_name, exist_ok=True)
            with open(os.path.join(file_name, "project_info.txt"), "w") as f:
                f.write(f"{os.path.abspath(file_name)}")
            temp_folder.set(Path(file_name))
        elif file_info:
            print(f"Uploading project file: {file_info['datapath']}")
            # validate project file
            with open(file_info["datapath"], "r") as f:
                for line in f:
                    content = line.strip()
                    break
                print(f"Project file content: {content}")
                content_path = Path(content)
                if not content_path.is_dir():
                    print(f"Invalid project file content: {content}")
                    return "Error: Invalid project file format."
            temp_folder.set(content_path)
        else:
            print("No project file or name provided.")   
        
    @output
    @render.ui
    def data_loaded():
        if data_loaded_correctly.get() is not None:
            if data_loaded_correctly.get():
                return ui.div(
                    ui.HTML('<span style="color:green;">✔</span>Data loaded successfully.')
                )
            else:
                return ui.div(
                    ui.HTML('<span style="color:red;">✖</span> Error loading data.')
                )


    @reactive.effect
    @reactive.event(input.load_data)
    def load_data():
        print("load_data running")
        try:
            if input.use_project_data():
                if temp_folder.get() is None:
                    print("No project loaded.")
                    return "Error: No project loaded."
                project_file = os.path.join(temp_folder.get(), "input_data.parquet")
                if not os.path.exists(project_file):
                    print(f"Project file {project_file} does not exist.")
                    return "Error: Project file does not exist."
                print(f"Loading data from project file: {project_file}")
                ui.notification_show(f"Loading data from project file: {project_file}\nThis can take a while...", type="message")
                vcf = VCFLoader(project_file, from_parquet=True)
                ui.notification_show(f"Data loaded from project file: {project_file}", type="message")
                vcf_object.set(vcf)
            else:
                file_info = input.data_file()[0] if input.data_file() else None
                if file_info is None:
                    print("No VCF file provided.")
                    return "Error: No VCF file provided."
                print(f"Loading data from VCF file: {file_info['datapath']}")
                ui.notification_show(f"Loading data from VCF file: {file_info['datapath']}\nThis can take a while...", type="message")
                vcf = VCFLoader(file_info["datapath"])
                ui.notification_show(f"Data loaded from VCF file: {file_info['datapath']}", type="message")
                output_file = os.path.join(temp_folder.get(), "input_data.parquet") if temp_folder.get() else "input_data.parquet"
                vcf.save_to_parquet(output_file)
                vcf_object.set(vcf)
            reload_project_text.set(f"Last update from load_data function: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            data_loaded_correctly.set(True)
        except Exception as e:
            print(f"Error loading data: {e}")
            data_loaded_correctly.set(False)
            return f"Error loading data: {e}"


    @output
    @render.text
    def project_info():
        print("project_info running")
        print(f"{reload_project_text.get()}")
        if temp_folder.get():
            tree_str = "\n".join(tree(temp_folder.get()))
            text_box = ui.div(
                ui.h4(f"Current project folder: {os.path.basename(temp_folder.get())}"),
                ui.pre(tree_str, style="font-family: monospace; white-space: pre-wrap")
            )

            return text_box
        else:
            return "No project loaded."
        
    @reactive.effect
    @reactive.event(input.run_analysis)
    def run_analysis():
        print("run_analysis running")
        if vcf_object.get() is None:
            print("No data loaded.")
            ui.notification_show("No data loaded. Please load a VCF file or a project first.", type="error")
            analysis_finished_correctly.set(False)
            return "Error: No data loaded."
        else:
            if input.scan_by_snps():
                Scanner = ScannerBySNP
                output_folder = os.path.join(temp_folder.get(), "scan_by_snps_results") if temp_folder.get() else "scan_by_snps_results"
            elif input.scan_by_position():
                Scanner = ScannerByPos
                output_folder = os.path.join(temp_folder.get(), "scan_by_position_results") if temp_folder.get() else "scan_by_position_results"
            else:
                print("No scanning method selected.")
                ui.notification_show("No scanning method selected. Please select a scanning method.", type="error")
                analysis_finished_correctly.set(False)
                return "Error: No scanning method selected."
            try:
                window_sizes = [int(x) for x in input.window_sizes().splitlines() if x.strip()]
                step_sizes = [int(x) for x in input.step_sizes().splitlines() if x.strip()]
                print(f"Window sizes: {window_sizes}")
                print(f"Steps: {step_sizes}")
                ui.notification_show(f"Running analysis with window sizes: {window_sizes} and steps: {step_sizes}\nThis can take a while...", type="message")
                scan = Scanner(
                    vcf_object = vcf_object.get(),
                    chrom=None,
                    window_size=window_sizes,
                    step=step_sizes,
                    force_windowstep=False,
                )
                scan.run_scan()
                scan.save_to_parquet(output_folder)



                ui.notification_show(f"Analysis finished. Results saved to {output_folder}", type="message")
                analysis_finished_correctly.set(True)
            except Exception as e:
                print(f"Error running analysis: {e}")
                ui.notification_show(f"Error running analysis: {e}", type="error")
                analysis_finished_correctly.set(False)
                return f"Error running analysis: {e}"
    

    @output
    @render.ui
    def analysis_finished():
        if analysis_finished_correctly.get() is not None:
            if analysis_finished_correctly.get():
                return ui.div(
                    ui.HTML('<span style="color:green;">✔</span>Analysis finished successfully.')
                )
            else:
                return ui.div(
                    ui.HTML('<span style="color:red;">✖</span> Error running analysis.')
                )