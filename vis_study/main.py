import logging

from generation import GenerationRequest, DataFormat, Renderer, generate_chart, remove_all_generated_files, \
    generate_index

if __name__ == "__main__":

    remove_all_generated_files()

    requests = []
    for i, num_data_points in enumerate([1000, 10_000, 50_000, 100_000]):

        request = GenerationRequest(
            experiment_name=str(i),
            num_points=num_data_points,
            num_categories=14,
            width=500,
            height=500,
            data_format=DataFormat.CSV,
            num_attributes=1,
            renderer=Renderer.CANVAS
        )
        logging.info(f"generating for {num_data_points}")
        generate_chart(request)
        requests.append(request)

    generate_index()
