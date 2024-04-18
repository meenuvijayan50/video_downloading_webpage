
import os

from django.core.serializers import json
from django.http import HttpResponse
from django.shortcuts import render, redirect
import requests

from django.views.decorators.csrf import csrf_exempt
from instaloader import Instaloader, Post
import base64


from tiktokapipy.api import TikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import video_link
import asyncio
from vimeo_downloader import Vimeo

from .forms import URLForm
@csrf_exempt
def enter_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data['url']
            if url.startswith("https://www.instagram.com"):
                try:
                    response, title = get_video_info(url)
                    video_url = url
                    return render(request, 'success_page.html', {'title': title,'response': response, 'video_url': video_url})
                except Exception as e:
                    return HttpResponse("An error occurred while processing the URL: {}".format(str(e)), status=500)

            if url.startswith("https://vimeo.com/"):
                try:
                    thumbnail_url, video_title = get_vimeo_video_info(url)
                    video_url = url
                    print("check1//",video_url)

                    return render(request, 'vimeo_sucess_page.html',{'thumbnail_url': thumbnail_url, 'video_title':video_title, 'video_url':video_url})
                except Exception as e:
                    print("error",str(e))
                    return HttpResponse("An error occurred while processing the URL: {}".format(str(e)), status=500)
            if url.startswith("https://www.tiktok.com/"):
                try:
                    thumbnail_url, title = get_video_thumbnail(url)
                    response = tiktok_download(url)
                    print("respone''''===",response)
                    return render(request, 'tiktok_success_page.html',{'thumbnail_url':thumbnail_url,'title': title, 'response': response })
                except Exception as e:
                    print("error",str(e))
                    return HttpResponse("An error occurred while processing the URL: {}".format(str(e)), status=500)
            else:
                return HttpResponse("URL is not from Instagram", status=400)
        else:
            return HttpResponse("Invalid form data", status=400)
    else:
        # If it's a GET request or a failed form submission, initialize the form with empty fields
        form = URLForm()

    return render(request, 'enter_url.html', {'form': form})


@csrf_exempt
def get_video_info(url):
    try:
        L = Instaloader()
        post = Post.from_shortcode(L.context, url.split("/")[-2])
        # Fetch video thumbnail
        thumbnail = post._full_metadata_dict['thumbnail_src']
        response = requests.get(thumbnail)
        image_data = base64.b64encode(response.content).decode('utf-8')  # Convert image content to base64
        title = post._full_metadata['edge_media_to_caption']['edges'][0]['node']['text']
        return image_data, title
    except Exception as e:
        raise e

@csrf_exempt
def show_success_page(request,url):
    try:
        response, title = get_video_info(url)
        return render(request, 'success_page.html', {'title': title, 'response': response})
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})


@csrf_exempt
def download_video(request):
    try:
        url = request.GET.get('url')
        print("Received URL:", url) # Extract the URL parameter from the request
        if url:
            # You might want to validate the URL here if needed
            L = Instaloader()
            post = Post.from_shortcode(L.context, url.split("/")[-2])
            print("Downloading video",post)
            if post.is_video:
                # Download the video
                target_filename = str(post.mediaid) + ".mp4"
                L.download_post(post, target=target_filename)

                # Set content disposition header for download
                response = HttpResponse("Video downloaded successfully")
                response['Content-Disposition'] = f'attachment; filename="{target_filename}"'
                return response
            else:
                return HttpResponse("The provided URL does not point to a video", status=400)
        else:
            return HttpResponse("URL parameter is missing", status=400)
    except Exception as e:
        return HttpResponse(f"Failed to download video: {str(e)}", status=500)
def get_vimeo_video_info(url):
    try:
        video_id = url.split('/')[-1]
        print("video_id", video_id)
        response = requests.get(f"https://vimeo.com/api/v2/video/{video_id}.json")

        if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
            video_data = response.json()[0]
            video_title = video_data.get('title')
            print("video_title", video_title)
            thumbnail_url = video_data.get('thumbnail_large')
            print("thumbnail.............", thumbnail_url)
            return thumbnail_url, video_title
        else:
            raise ValueError(f"Failed to fetch thumbnail for video: {url}")
    except Exception as e:
        raise e
# vimeo without resolution download
def vimeo_download(request):
    try:
        video_url = request.GET.get('url')

        response = requests.get(video_url)

                    # Check if the request was successful
        if response.status_code == 200:
                        # Save the video file locally
            video_path = 'video_tiktok.mp4'
            response = HttpResponse("Video downloaded successfully")
            response['Content-Disposition'] = f'attachment; filename="{video_path}"'
            return response
        else:
            return HttpResponse("The provided URL does not point to a video", status=400)

    except Exception as e:
        return HttpResponse(f"Failed to download video: {str(e)}", status=500)


    #VIMEO  resolution FUNCTIONS
# def get_available_resolutions(url):
#     try:
#         v = Vimeo(url)
#         video_formats = v.streams
#         resolutions = [stream.quality for stream in video_formats if stream.quality.isdigit()]
#         print("These are the available video formats:")
#         for stream in video_formats:
#             print(stream.quality)
#         print('resolutions///',resolutions)
#         return resolutions
#     except Exception as e:
#         raise e


# def vimeo_download_video(request):
#     if request.method == 'POST':
#         resolution = request.POST.get('resolution')
#         video_url = request.POST.get('url')
#
#         if not resolution:
#             # If resolution is not selected, get the last resolution from the dropdown
#             resolutions = request.POST.getlist('resolution')
#             if resolutions:
#                 resolution = resolutions[-1]
#
#         try:
#             # Download the video file using requests
#             response = requests.get(video_url)
#
#             # Check if the request was successful
#             if response.status_code == 200:
#                 # Save the video file locally
#                 video_path = 'video_with_resolution_{}.mp4'.format(resolution)
#                 with open(video_path, 'wb') as f:
#                     f.write(response.content)
#
#                 # Open the downloaded video file
#                 with open(video_path, 'rb') as video_file:
#                     # Return the video file as a response
#                     response = FileResponse(video_file)
#                     response['Content-Disposition'] = 'attachment; filename="video.mp4"'
#                     return response
#             else:
#                 return HttpResponse("Failed to download the video", status=response.status_code)
#         except Exception as e:
#             return HttpResponse("An error occurred: {}".format(str(e)), status=500)
#
#     return HttpResponse("Invalid request", status=400)
@csrf_exempt
def vimeo_success_page(request, url):
    try:
        thumbnail_url, video_title = get_vimeo_video_info(url)

        return render(request, 'vimeo_sucess_page.html',{'thumbnail_url':thumbnail_url,'video_title':video_title})
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})

#tiktok functions
@csrf_exempt
def get_video_thumbnail(url):
    with TikTokAPI() as api:
        # Fetch video information
        video = api.video(url)
        # Access the thumbnail URL from the video object
        thumbnail_url = video.video.cover
        title = video.desc
        return thumbnail_url,title

def tiktok_download(url):
    with TikTokAPI() as api:
        try:
            print("Attempting to download TikTok video from URL:", url)
            video = api.video(url)
            print('video:////',video)
            save_video(video, api)
            response = HttpResponse("Video downloaded successfully")
            return response
        except Exception as e:
            print(f"Error downloading video: {e}")
            return HttpResponse(f"Error downloading video: {e}")

def save_video(video, api):
    cookies = {cookie["name"]: cookie["value"] for cookie in api.context.cookies() if cookie["name"] == "tt_chain_token"}
    with requests.Session() as session:
        resp = session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}, cookies=cookies)
        if resp.status_code == 200:
            filename = f"{video.id}.mp4"
            script_path = os.path.dirname(__file__)
            filepath = os.path.join(script_path, filename)
            with open(filepath, 'wb') as f:
                f.write(resp.content)




def tiktok_success_page(request,url):
    try:
       thumbnail_url,title = get_video_thumbnail(url)

       return render(request, 'tiktok_sucess_page.html',{'thumbnail_url':thumbnail_url,'title': title })
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})
