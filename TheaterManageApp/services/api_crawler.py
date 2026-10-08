import os
import time
import requests
import json

class MovieCrawler:
    def __init__(self, api_key="4745010e7edb2bcabed69a949bbf641b"):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w300"

    def _make_request(self, url, retries=3, delay=0.5):
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(f"[Warn] API Request failed: {e}")
                time.sleep(delay * (2 ** attempt))
        return {}

    def get_now_showing_movies(self, pages=1):
        results = []
        for page in range(1, pages + 1):
            url = f"{self.base_url}/movie/now_playing?api_key={self.api_key}&language=vi-VN&page={page}&region=VN"
            data = self._make_request(url)
            results.extend(data.get("results", []))
        return results

    def get_upcoming_movies(self, pages=1):
        results = []
        for page in range(1, pages + 1):
            url = f"{self.base_url}/movie/upcoming?api_key={self.api_key}&language=vi-VN&page={page}&region=VN"
            data = self._make_request(url)
            results.extend(data.get("results", []))
        return results

    def get_movie_details(self, movie_id):
        if not movie_id: return {}
        url = f"{self.base_url}/movie/{movie_id}?api_key={self.api_key}&language=vi-VN&append_to_response=credits"
        data = self._make_request(url)
        
        crew = data.get("credits", {}).get("crew", [])
        director = next((c["name"] for c in crew if c.get("job") == "Director"), "N/A")
        cast = [c["name"] for c in data.get("credits", {}).get("cast", [])[:5]]
        
        return {
            "genres": data.get("genres", []),
            "runtime": data.get("runtime", 120),
            "cast": cast,
            "director": director,
            "showtimes": []
        }

    # --- ĐÃ KHÔI PHỤC HÀM NÀY ĐỂ SỬA LỖI 1 ---
    def get_age_rating(self, movie_id):
        if not movie_id: return "P"
        url = f"{self.base_url}/movie/{movie_id}/release_dates?api_key={self.api_key}"
        data = self._make_request(url)
        
        rating = "P" 
        for result in data.get("results", []):
            iso = result.get("iso_3166_1")
            if iso == "VN":
                for rel in result.get("release_dates", []):
                    cert = rel.get("certification")
                    if cert: return cert
            elif iso == "US" and rating == "P":
                for rel in result.get("release_dates", []):
                    cert = rel.get("certification")
                    if cert: rating = cert
        return rating

    def download_poster(self, poster_path, movie_id):
        if not poster_path or not movie_id: return None
        
        # Dùng đường dẫn tuyệt đối
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        poster_dir = os.path.join(base_dir, "images", "posters")
        try: os.makedirs(poster_dir, exist_ok=True)
        except: pass
        
        file_name = f"poster_{movie_id}.jpg"
        file_path = os.path.join(poster_dir, file_name)

        if os.path.exists(file_path): return file_path

        url = f"{self.image_base_url}{poster_path}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                return file_path
        except: pass
        return None