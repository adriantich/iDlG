from htmltools import css
from shiny import ui
from .layout_tools import *


def app_ui():
    """Simple app layout composing the components."""
    return ui.page_fluid(
        ui.layout_sidebar(
            ui.sidebar(
                "Project", 
                ui.output_ui("project_info"),
                width=450,
                bg="#f8f8f8",
                resizable=True,
            ),  
            ui.h1("iDlG"),
            ui.page_navbar(
                ui.nav_panel(
                    "Home",
                    ui.h4("Welcome to iDlG!"),
                    ui.p("This application allows to scan genomes for chromosome inversions."),
                    ui.p("Please, create a new project or load an existing one to start using the application."),
                    ui.br(),
                    ui.input_text("project_name", "Project name"),
                    ui.input_file("project_file", "Input"),
                    ui.br(),
                    ui.input_action_button("create_project", "Load project", width="25%"),
                ),
                ui.nav_panel(
                    "Experiment",
                    ui.row(
                        ui.h4("1 - Load data"),
                        ui.p("Load a VCF file containing the genomic data to be analyzed."),
                        ui.input_file("data_file", "Input vcf file"),
                        ui.p("If this is not the first time you are using this application, you can load a previously created project by selecting the project file 'input_data.parquet'."),
                        ui.input_checkbox("use_project_data", "Use data from Project", False),
                    ),
                    ui.row(
                        ui.column(
                            2,
                            ui.input_action_button("load_data", "Load vcf data"),
                            ui.output_ui("data_loaded"),
                        ),
                    ),
                    ui.br(),
                    ui.row(
                        ui.column(
                            4,
                            # add a file selector input
                            ui.row(
                                ui.h4("2 - Scan data"),
                                ui.p("Select the scanning method and parameters to analyze the genomic data."),
                                ui.input_checkbox("scan_by_snps", "Scan by SNPs", True),
                                ui.input_checkbox("scan_by_position", "Scan by Position", False),
                            ),
                        ),
                    ),
                    ui.row(
                        ui.h4("3 - Set scanning parameters"),
                        ui.p("Set the scanning parameters for the selected method."),
                        ui.column(
                            4,
                            ui.row(
                                ui.input_text_area(
                                    id = "step_sizes",
                                    rows = 5,
                                    label = "Step size (one value per line)",
                                    value="500\n1500\n2500",
                                    width="100%",
                                )
                            ),
                        ),
                        ui.column(
                            4,
                            ui.row(
                                ui.input_text_area(
                                    id = "window_sizes",
                                    rows = 5,
                                    label = "Window sizes (one value per line)",
                                    value="500\n1500\n2500",
                                    width="100%",
                                )
                            ),
                        ),
                    ),
                    ui.row(
                        ui.h4("4 - Run scan"),
                        ui.p("Run the scanning process with the selected parameters."),
                        ui.input_action_button("run_analysis", "Run scan"),
                        ui.output_ui("analysis_finished"),
                    )
                ),
                ui.nav_panel(
                    "Plots",
                    ui.br(),
                    ui.p("This section will allow you to visualize the graphical representation of the genomic data."),
                    ui.row(
                        "Parameters",
                        ui.column(
                            5,
                            ui.h4("Units"),
                            ui.input_checkbox("plot_by_snps", "Plot scan by SNPs", True),
                            ui.input_checkbox("plot_by_position", "Plot scan by Position", False),
                            ui.br(),
                            ui.h4("Chromosome"),
                            ui.output_ui(
                                "selected_chromosome",
                            ),
                        ),
                        ui.column(
                            5,
                            ui.h4("Step and Window sizes"),
                            ui.output_ui(
                                "selected_step_size",
                            ),
                            ui.output_ui(
                                "selected_window_size",
                            ),
                        ),
                    ),
                    ui.row(
                        ui.h4("Plot"),
                        ui.input_action_button("create_plot", "Refresh plot"),
                        ui.output_ui("scan_plot"),
                    ),
                    # ui.br(),
                    # ui.p("Warning:"),
                    # ui.p("Haplotype storage in Map should have been enabled before querying. "),
                    # ui.p("Create or load a project first."),
                    # ui.row(
                    #     ui.h3("Edit table before plotting"),
                    #     ui.column(
                    #         5,
                    #         ui.h4("Samples table"),
                    #         samples_table("sample_colors"),
                    #     ),
                    #     ui.column(
                    #         5,
                    #         ui.h4("Samples coords"),
                    #         sample_plot("coordinates_plot")
                    #     ),
                    # ),
                    # ui.row(
                    #     ui.h4("Haplotype Network"),
                    #     ui.column(
                    #         4,
                    #         ui.output_ui("haplonet_ui"),
                    #         run_button("btn_run_haplonet", "Run MetaPhyloTools"),
                    #         ui.br(),
                    #         export_selected_button("btn_export_haplotypes", "Export haplotypes"),
                    #     ),
                    #     ui.column(
                    #         6,
                    #         ui.output_ui("render_haplonet"),
                    #     ),
                    # ),
                ),
            ),
        )
        
    )