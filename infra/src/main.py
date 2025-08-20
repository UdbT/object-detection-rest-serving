

from cdktf import App

from src.infrastructure.components import ObjectDetectionStack

app = App()
ObjectDetectionStack(app, "ObjectDetectionStack")
app.synth()
