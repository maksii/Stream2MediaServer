
from providers.generic_provider import GenericProvider


def main():
    config = {}  # Configuration settings if any
    provider = GenericProvider(config)

    # Example to search titles
    search_query = "Брама"
    search_results = provider.search_title(search_query)
    for result in search_results:
        print(f"Found: {result.title} - {result.title_eng}")

    # Assuming the user selects the first result
    selected_result = search_results[0]

    # Load details page for the selected movie
    series_list = provider.load_details_page(selected_result.link)

    # Assuming the user selects the first series
    selected_series = series_list[0]

    # Download and concatenate the series into a single file
    #final_video_path = provider.download_and_concatenate_series(selected_series.url)
    #print(f"Video has been processed and saved to {final_video_path}")
    print("No Actions. Stream2MediaServer")
    
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