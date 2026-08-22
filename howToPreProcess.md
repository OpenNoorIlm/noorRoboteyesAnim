# How to PreProcess Animated videos?

- First go to animationStuff -> animations -> animation.
- Now accordingly split all the videos having (.*?)_mjpeg.avi like this:
    - First create a folder by their name example (.*?)_mjpeg.
    - Then in the created folder split the (.*?)_mjprg.avi by 10 frames at 12fps as generated in blender so we can cut exactly where an the animation   face starts and ends **IMPORTANT ON WHAT TO NAME THE FILES NAME BY E=EYES M=MOUTH KF=KEYFRAME SO CREATE BY F"E{KF}||M{KF}"** and also you would have to extract exactly 1st frame of each animation as an image which you will see why soon and save them in folder Static folder because we also need where eyes and mouth are still.
    - Then after all the splitting and naming those files now we create the API which can be used by a python script in.
    - We will create the API in JSON then convert it to DB because of how many animations there are it is good to keep speed.
    - Now here is the structure on how the json should look but you can make it more robust!
```json
            {
    "config":{
        "EBasis||MBasis":"Static/EBasis||MBasis.mjpeg",
        "EAngry||MBasis":"onlyEyes_mjpeg/EAngry||MBasis.avi",
        "...":"..."
    },

    "EBasis||MBasis":{
        "description":"In this animation the Eyes and Mouth both are still, and the animation is only for the background. And the in the animation the Eye is a rectangular rounded shape and the Mouth is a rectangular stretched shape.",
        "timeline":{
            "0-5":"The Eyes and Mouth are still no action.",
            "5-10":"The Eyes and Mouth are still no action."
        }
    },

    "EAngry||MBasis":{
        "description":"In this animation the Eyes are angry and the Mouth is still, and the animation is only for the background. (describe it more briefly)...).",
        "timeline":{
            "0-5":"The Eyes are angrily closing and the Mouth is still no action.",
            "5-10":"The Eyes are angrily opeing again and the Mouth is still no action."
        }
    }

}
```
 - Then finally convert the json into db.