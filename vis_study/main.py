from spec_generation import GenerationRequest, DataFormat, Renderer, generate, remove_all_generated_files

if __name__ == "__main__":

    remove_all_generated_files()

    request = GenerationRequest(
        experiment_name="exp_300k_canvas_csv",
        num_points=3000,
        num_categories=14,
        width=500,
        height=500,
        data_format=DataFormat.CSV,
        num_attributes=5,
        renderer=Renderer.CANVAS
    )

    generate(request)
