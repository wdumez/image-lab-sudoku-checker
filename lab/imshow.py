from __future__ import print_function
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
from IPython.display import *

import os
import io
import base64
from base64 import b64decode


import cv2
import numpy as np
import matplotlib.pyplot as plt
import copy

import IPython
from google.colab import output
from google.colab.output import eval_js

import mpld3
from mpld3 import plugins

import time
from tqdm import tqdm_notebook as tqdm



__all__ = ["imshow", "grid_imshow", "click_imshow", "show_video", "take_photo"]

def imshow(image,
        figsize = (10, 10),
        title = None,
        bgr2rgb = False,
        savefig = None):

    #Take a copy of the image
    tmp_image = copy.deepcopy(image)

    # Create a new figure
    plt.figure(figsize = figsize)

    if title is not None:
        plt.title(title)

    # Disable plt axises
    plt.axis('off')

    # Check wheter the image contains 3 colours
    if len(tmp_image.shape) == 3 and tmp_image.shape[2] == 3: #Swap R en B colour
        if bgr2rgb:
            tmp_image = tmp_image[: ,: , (2, 1, 0)]
        plt.imshow(tmp_image)
    else:
        #In case ofa single channel, set matplotlib to plot a gray image
        plt.imshow(tmp_image, cmap = plt.cm.gray)
        
    if savefig is not None:
        plt.savefig(savefig)


def grid_imshow(images,
        gridsize = (2, 2),
        figsize = (10, 10),
        title = None,
        subtitles = None,
        bgr2rgb = False,
        savefig = None):

    #Create a new figure
    nrows, ncols = gridsize
    fig, subplots = plt.subplots(nrows, ncols, figsize=figsize, 
                                 sharex=False, sharey=False, clear=True)

    subplots = subplots.reshape(nrows*ncols)

    if title is not None:
        fig.suptitle(title)
   
    for i, image in enumerate(images):
        subplot = subplots[i]

        if subtitles is not None:
            subplot.set_title(subtitles[i])

        # Take a copy of the image
        tmp_image = copy.deepcopy(image)

        # Disable plt axises
        subplot.axis('off')

        # Check wheter the image contains 3 colours
        if len(tmp_image.shape) == 3 and tmp_image.shape[2] == 3: #Swap R en B colour
            if bgr2rgb:
                tmp_image = tmp_image[: ,: , (2, 1, 0)]
            subplot.imshow(tmp_image)
        else:
            #In case ofa single channel, set plot a gray image
            subplot.imshow(tmp_image, cmap=plt.cm.gray)

        
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
    
    if savefig is not None:
        fig.savefig(savefig)
            
    fig.show()


class MouseClickPosition(mpld3.plugins.PluginBase):
    """Like MousePosition, but on click will callback a Google Colab X/Y position"""

    JAVASCRIPT="""
  mpld3.register_plugin("mouseclickposition", MouseClickPosition);
  MouseClickPosition.prototype = Object.create(mpld3.Plugin.prototype);
  MouseClickPosition.prototype.constructor = MouseClickPosition;
  MouseClickPosition.prototype.requiredProps = [];
  MouseClickPosition.prototype.defaultProps = {colab_callback_id: ''};
  function MouseClickPosition(fig, props) {
    mpld3.Plugin.call(this, fig, props);
  }
  MouseClickPosition.prototype.draw = function() {
    var fig = this.fig;
    var fmt = d3.format(".3g");

    var colab_callback_id = this.props.colab_callback_id;
    
    var coords = fig.canvas.append("text").attr("class", "mpld3-coordinates").style("text-anchor", "end").style("font-size", this.props.fontsize).attr("x", this.fig.width - 5).attr("y", this.fig.height - 5);
    for (var i = 0; i < this.fig.axes.length; i++) {
      var update_coords = function() {
        var ax = fig.axes[i];
        return function() {
          var pos = d3.mouse(this), x = ax.x.invert(pos[0]), y = ax.y.invert(pos[1]);
          coords.text('(' + fmt(x) + '; ' + fmt(y) + ')');
        };
      }();


      var click_coords = function() {
          var ax = fig.axes[i];
          return function() {
            var pos = d3.mouse(this), x = ax.x.invert(pos[0]), y = ax.y.invert(pos[1]);
            google.colab.kernel.invokeFunction('notebook.clickImage'+colab_callback_id, [x, y], {});
          };
      }();

      fig.axes[i].baseaxes.on("mousemove", update_coords);
      fig.axes[i].baseaxes.on("mousedown", click_coords);

    }

  };
  
  """
    def __init__(self, colab_callback_func, colab_callback_id):
      output.register_callback('notebook.clickImage'+colab_callback_id, colab_callback_func)

      self.dict_ = {"type": "mouseclickposition",
                    "colab_callback_id": colab_callback_id}

def click_imshow(image,
        callback,
        callback_id="",
        figsize = (10, 10),
        title = None,
        bgr2rgb = False):

    #Take a copy of the image
    tmp_image = image.copy()

    # Create a new figure
    fig, ax = plt.subplots(figsize=figsize)

    if title is not None:
      ax.set_title(title)


    # Disable plt axises
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    # Check wheter the image contains 3 colours
    if len(tmp_image.shape) == 3 and tmp_image.shape[2] == 3: #Swap R en B colour
        if bgr2rgb:
            tmp_image = tmp_image[: ,: , (2, 1, 0)]
        ax.imshow(tmp_image)
    else:
        #In case ofa single channel, set matplotlib to plot a gray image
        ax.imshow(tmp_image, cmap = plt.cm.gray)

    plugins.connect(fig, MouseClickPosition(colab_callback_func=callback,
                                            colab_callback_id=callback_id))


def show_video(filename):
    os.system(f'ffmpeg -y -loglevel panic -i  {filename} -an /out.mp4')  

    video = io.open('/out.mp4', 'r+b').read()
    encoded = base64.b64encode(video)
    return HTML(data='''<video alt="test" width="800" webkitallowfullscreen=true mozallowfullscreen=true controls>
                    <source src="data:video/mp4;base64,{0}" type="video/mp4"/>
                 </video>'''.format(encoded.decode('ascii')))


def take_photo(quality=1.0):
  js = Javascript('''
    async function takePhoto(quality) {
      const div = document.createElement('div');
      const capture = document.createElement('button');
      capture.textContent = 'Capture';
      div.appendChild(capture);

      const video = document.createElement('video');
      video.style.display = 'block';
      const stream = await navigator.mediaDevices.getUserMedia({video: true});

      document.body.appendChild(div);
      div.appendChild(video);
      video.srcObject = stream;
      await video.play();

      // Resize the output to fit the video element.
      google.colab.output.setIframeHeight(document.documentElement.scrollHeight, true);

      // Wait for Capture to be clicked.
      await new Promise((resolve) => capture.onclick = resolve);

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      stream.getVideoTracks()[0].stop();
      div.remove();
      return canvas.toDataURL('image/jpeg', quality);
    }
    ''')
  display(js)
  data = eval_js('takePhoto({})'.format(quality))
  binary = b64decode(data.split(',')[1])

  return cv2.imdecode(np.frombuffer(binary, dtype=np.uint8), -1)


