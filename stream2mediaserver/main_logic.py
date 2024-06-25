
def add_release_by_url(config):
    pass

def add_release_by_name(config):
    pass
    
def update_release_by_name(config):
    pass
    
def update_releases(config):
    pass

def update_release(config):
    pass

import concurrent.futures
from importlib import import_module

# List of provider class names to be dynamically loaded and queried
provider_mapping = {
    "animeon_provider": "AnimeOnProvider",
    "anitube_provider": "AnitubeProvider",
    "uakino_provider": "UakinoProvider",
    "uaflix_provider": "UaflixProvider"
}

def get_provider_class(provider_name):
    file_name = provider_name.lower()
    class_name = provider_mapping[file_name]
    try:
        module = import_module(f"providers.{file_name}")
        return getattr(module, class_name)
    except ImportError:
        try:
            # Fallback to the package-specific import
            module = import_module(f"stream2mediaserver.providers.{file_name}")
            return getattr(module, class_name)
        except ImportError as e:
            print(f"Failed to import {class_name} from {file_name} in both default and fallback namespaces: {e}")
    except AttributeError as e:
        print(f"Class {class_name} not found in module {file_name}: {e}")

def search_titles(provider_class, query):
    config = {}  # Configuration settings if any
    provider = provider_class(config)
    return provider.search_title(query)

def search_releases(config):
    search_query = config.args.query
    results = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_provider = {}
        for provider_name in provider_mapping:
            provider_class = get_provider_class(provider_name)
            if provider_class:
                future = executor.submit(search_titles, provider_class, search_query)
                future_to_provider[future] = provider_name
            else:
                print(f"Provider {provider_name} could not be loaded.")

        for future in concurrent.futures.as_completed(future_to_provider):
            provider_name = future_to_provider[future]
            try:
                provider_results = future.result()
                results.extend(provider_results)  # Assuming each result is a list of results
                print(f"Results from {provider_name} received.")
            except Exception as exc:
                print(f"{provider_name} generated an exception: {exc}")
    
    return results

def search_releases_for_provider(provider_name, query):
    provider_class = get_provider_class(provider_name)
    if provider_class:
        return search_titles(provider_class, query)
    return []

def get_release_details(provider_name, release_url):
    provider_class = get_provider_class(provider_name)
    if provider_class:
        provider_instance = provider_class({})
        return provider_instance.load_details_page(release_url)

def get_details_for_all_releases(releases):
    details = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_details = {executor.submit(get_release_details, release['provider'], release['url']): release for release in releases}
        for future in concurrent.futures.as_completed(future_to_details):
            release = future_to_details[future]
            try:
                details.append(future.result())
            except Exception as exc:
                print(f"Error retrieving details for {release['url']}: {exc}")
    return details