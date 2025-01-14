# Dash Router 

## Core Concepts 

Compared to the normal dash pages system, where a flat dict with direct routes is used to navigate the app, `dash-router` creates a route and execution tree. This enables a segment wise rendering where every selected child layout gets inserted into the parent layout. 

Routes get determined by the folder structure and need some file conventions to provide the `slots` and `parallel routes` features. The router builds a route tree at instatiation by traversing the `pages` folder and looking for `page.py` files which have to contain eather a layout function or component. 

Url segments are your folder names in order to 

### Path Template


```python



```

### Slots 

Slots are silent url segments which don't affect the url, one or none dynamic and take a path template, 


### Parallel Routes / View templates 

