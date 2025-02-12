"""Main entry point for stream2mediaserver."""

import concurrent.futures
from importlib import import_module
from types import SimpleNamespace

from .main_logic import (
    get_details_for_all_releases,
    get_release_details,
    search_releases,
    search_releases_for_provider
)

def main():
    # Test search for a specific provider
    anitube_results = search_releases_for_provider("anitube_provider", "The New Gate")
    if anitube_results:
        anitube_details = get_release_details("anitube_provider", anitube_results[0].link)
    
    uakino_results = search_releases_for_provider("uakino_provider", "The New Gate")
    if uakino_results:
        uakino_details = get_release_details("uakino_provider", uakino_results[0].link)
    
    print("Stream2MediaServer initialized")
    
        #config = SimpleNamespace(args=SimpleNamespace(query="The New Gate"))
    #results_all = search_releases(config)
    #for result in results_all:
    #    print(f"Found: {result.provider} - {result.title}")
        #details_all = get_details_for_all_releases(results_all)
    
    #search_query = "Брама"
    #results = []
    #
    ## Using ThreadPoolExecutor to manage a pool of threads
    #with concurrent.futures.ThreadPoolExecutor() as executor:
    #    # Future objects for each provider search
    #    future_to_provider = {
    #        executor.submit(search_titles, import_module(f"providers.{file_name}").__dict__[class_name], search_query): class_name
    #        for file_name, class_name in provider_mapping.items()
    #    }
#
    #    # Collecting results as they complete
    #    for future in concurrent.futures.as_completed(future_to_provider):
    #        provider_name = future_to_provider[future]
    #        try:
    #            provider_results = future.result()
    #            results.extend(provider_results)  # Assuming each result is a list of results
    #            print(f"Results from {provider_name} received.")
    #        except Exception as exc:
    #            print(f"{provider_name} generated an exception: {exc}")
#
    ## Printing all results
    #for result in results:
    #    print(f"Found: {result.provider} - {result.title}")
        
    #config = {}  # Configuration settings if any
    #provider = GenericProvider(config)

    # Example to search titles
    #search_query = "The New Gate"
    #search_results = provider.search_title(search_query)
    #for result in search_results:
    #    print(f"Found: {result.name} - {result.original_name}")

    # Assuming the user selects the first result
    #selected_result = search_results[0]

    # Load details page for the selected movie
    #series_list = provider.load_details_page(selected_result.url)

    # Assuming the user selects the first series
    #selected_series = series_list[0]

    # Download and concatenate the series into a single file
    #final_video_path = provider.download_and_concatenate_series(selected_series.url)
    #print(f"Video has been processed and saved to {final_video_path}")

    
    ##case: generic  
    #load config
    #detect providers
    
    ##case: download
    #geturl
    #download
    #create torrent
    #add torrent
    #save operation status \ update config
    
    
    ##case: details
    #get into details
    #parse voice studio and season\series
    #get playlist
    
    
    ###case1: Add new
    ##case:generic
    #get search term
    #foreach provider search
    #ask user to select result
    ##case:details
    ##case:download
    
    
    ###case2: refresh
    ##case:generic
    #read titles
    #foreach title ##case:download
    

if __name__ == "__main__":
    main()