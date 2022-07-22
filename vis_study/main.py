import logging

from generation import GenerationRequest, DataFormat, Renderer, generate_chart, remove_all_generated_files, \
    generate_index

if __name__ == "__main__":

    remove_all_generated_files()

    requests = []

    i = 1

    for renderer in [Renderer.CANVAS, Renderer.SVG]:
        for output_format in [DataFormat.JSON, DataFormat.CSV]:
            for num_data_points in [1000, 5_000, 10_000, 30_000]:
                request = GenerationRequest(
                    experiment_name=f"{i:02}",
                    num_points=num_data_points,
                    num_categories=14,
                    width=500,
                    height=500,
                    data_format=output_format,
                    num_attributes=2,
                    renderer=renderer
                )
                logging.info(f"generating for {num_data_points}")
                generate_chart(request)
                requests.append(request)
                i += 1

        generate_index()
