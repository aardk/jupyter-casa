FROM penngwyn/jupytercasa

USER jupyter
RUN echo "c.NotebookApp.token = ''" >> /home/jupyter/.jupyter/jupyter_notebook_config.py
ENV DISPLAY :102
ADD --chown=jupyter:jupyter 3c391_ctm_mosaic_20s_4mhz_spw0.ms.tgz /home/jupyter
COPY --chown=jupyter:jupyter vla-cont-demo.ipynb /home/jupyter
