from flask import Flask
from flask import request
from flask import Response
from flask import make_response
from flask import send_file
from werkzeug.datastructures import Headers
import logging
import logging.handlers
from imagehandler import imagehandler

app = Flask(__name__)

mylogger = logging.getLogger("dynamicimgprocessor")
mylogger.addHandler(logging.handlers.RotatingFileHandler("/var/www/imgprocessor/dynamicimgprocessor.log",'a',100000,5))
mylogger.setLevel("INFO")

#Key variables which will be used for generating the image.
filename =""
bwidth=""
screensize = ""
forcesize=0
width=0
height =0

@app.route("/")
def respond_image():
    '''
    This application is standalone server which internally calls the class:imghandler that outputs the byte of image without local storage.
    In case you need the path to the file or json, will directly need to integrate with  class: imgprocessor
    Querystring accepted are below. Only filename is mandatory.
    --name = "Path or name of the image". Note that imagehandler has a path config which will be used with this value to load the file
    --width = width of image to generate
    --height = height of image to generate
    --fsize = forcesize the image i.e. if 1, it will not keep aspect ratio and blindly resizes image, else it would keep aspect ratio and generate image based on WxH given

    Header - Both are optional headers used more for native app optimizations. Need to ensure headernames are same as given below:
    --HTTP_SCREENSIZE - This is the screensize used for dynamic scaledown of image would happen. Use this for mobile apps.
    Optimization logic written for values of 320, 360,480, 540, 1080, 720, 640, 240.
    --HTTP_NW_TYPE : This can be 2g,3g,4g or *. This is network type , * means anything outside 2g,3g,4g used more for desktops

    if both HTTP_SCREENSIZE,HTTP_NW_TYPE with width & height is given, width & height is considered along with HTTP_NW_TYPE.
    if width & height with HTTP_NW_TYPE is given then the same would be considered for image optimization in terms of size.
    if none are given HTTP_SCREENSIZE is assumed to be 1080, HTTP_NW_TYPE = *
    '''
    try:

        #Resolve Imagename, height,width & fsize in querystring
        if len(request.args) >0:
            filename = request.args.get("name")
            if not (request.args.get("width") == "NoneType"):
                try:
                    width = int(request.args.get("width"))
                except:
                    width = 0
            if not (request.args.get("height") == "NoneType"):
                try:
                    height = int(request.args.get("height"))
                except:
                    height = 0
            if not (request.args.get("fsize") == "NoneType"):
                try:
                    forcesize = request.args.get("fsize")
                    #if input value is other than 0 or 1, set forcesize as 0 i.e.false
                    if not (forcesize == "1"):
                        forcesize = False
                    else:
                        forcesize = True
                except Exception as ex:
                    mylogger.error(ex)
                    forcesize = False

        #Resolve all header info which has screensize & bandwidth
        if request.headers.get("HTTP_NW_TYPE") == 'NoneType':
            bwidth = "2g"
        else:
            bwidth = str(request.headers.get("HTTP_NW_TYPE"))

        if request.headers.get("HTTP_SCREENSIZE") == 'NoneType':
            screensize = "320"
        else:
            screensize = str(request.headers.get("HTTP_SCREENSIZE"))
    except Exception as ex:
        mylogger.error("Error while parsing input keys for {} - Exception : {}".format(filename, ex))

    #Now get the image based on resolved values from the request
    responseimage = generate_image(filename,width,height,forcesize,bwidth,screensize)

    #Comple the key and set the value as imagekey
    if (height > 0 or width > 0):
        if len(bwidth) == 0 or bwidth == "None":
            returnquerystring = "{}_{}x{}".format(filename, width, height)
        else:
            returnquerystring = "{}_{}x{}_{}".format(filename, width, height, bwidth)
    else:
        if not (screensize == "None") and not (bwidth == "None"):
            returnquerystring = "{}_{}_{}".format(filename, screensize, bwidth)
        elif not (screensize == "None") and bwidth == "None":
            returnquerystring = "{}_{}".format(filename, screensize)
        elif screensize == "None" and not (bwidth == "None"):
            returnquerystring = "{}_{}".format(filename, bwidth)
        else:
            returnquerystring = filename

    mylogger.info("Generated image for {}".format(returnquerystring))
    #responseimage = "<html><body></body></html>"

    #Add the responseimage back using make_response and also headers for ContentType,Length, Server & imagekey
    response = make_response(responseimage)
    response.headers.add("Content-Type",'image/jpeg')
    response.headers.add("Content-Length",  str(len(responseimage)))
    response.headers.add("Server", "Encrypt")
    response.headers.add("imagekey", returnquerystring)
    return response

def generate_image(filename,width,height,forcesize,bwidth,screensize):
    '''
    :param filename: "Path or name of the image". Note that imagehandler has a path config which will be used with this value to load the file
    width = width of image to generate
    :param width: width of image to generate
    :param height: height of image to generate
    :param forcesize: forcesize the image i.e. if 1, it will not keep aspect ratio and blindly resizes image, else it would keep aspect ratio and generate image based on WxH given
    :param bwidth: This can be 2g,3g,4g or *. This is network type , * means anything outside 2g,3g,4g used more for desktops
    :param screensize: This is the screensize used for dynamic scaledown of image would happen. Use this for mobile apps.
    Optimization logic written for values of 320, 360,480, 540, 1080, 720, 640, 240.
    :return: 
    '''
    try:

        #Load the imagehandler and get the response image. This module resolves the image and returns the value
        img =imagehandler()
        mylogger.info("Generate image for name:{},ssize:{},bwidth:{},w:{},h:{},force:{}".format(filename, screensize, bwidth, width,
                                                                                 height, forcesize))
        response_body = img.generate(filename, ssize=screensize, band=bwidth, width=width, height=height,
                                     forcesize=forcesize)
    except Exception as ex:
        mylogger.error("Issue in generating image for {} - exceptiontrace:{}".format(filename,ex))
    #Return the imagebody
    return response_body

@app.errorhandler(404)
def errorhandler404(error):
    '''
    This is to handle any HTTP 404 error response. It generates a generic 404image.png. It can be placed in the common
    image repo and the name has to be 404image.png
    :param error: This is default framework value incoming based on httpresponse from the call in the app.route
    :return: Returns the 404image.png using bandwidth/screensize or width & height
    '''
    response = handleerrorimage()
    mylogger.error("404image rendered because {} not found".format(filename))
    return response,404

@app.errorhandler(500)
def errorexception500(error):
    '''
    This is to handle any HTTP 500 error response
    :param error:This is default framework value incoming based on httpresponse from the call in the app.route
    :return: Returns just a string "error" for now with header imagekey as error
    '''
    response = handleerrorimage()
    mylogger.error("500 error rendered because {} not found".format(filename))
    return response,500

def handleerrorimage():
    img = imagehandler()
    errorresponse = img.generate("404image.png", ssize=screensize, band=bwidth,
                                 width=width, height=height, forcesize=forcesize)
    errorresponse = make_response(errorresponse)
    errorresponse.headers.add("Content-Type", 'image/jpeg')
    errorresponse.headers.add("Server", "Encrypt")
    errorresponse.headers.add("imagekey", "404image.png")
    return errorresponse



if __name__ == "__main__":
    app.run(debug=False)