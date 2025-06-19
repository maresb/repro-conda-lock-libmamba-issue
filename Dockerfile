FROM quay.io/jupyter/minimal-notebook@sha256:fa912aec1c8935c2422c9b14d02229ec3824d50cbe333c6faddedb0fb63af506

USER root

ENV MAMBA_ROOT_PREFIX=/opt/conda

# Silence 'WARNING: /opt/conda/etc/profile.d/mamba.sh (the file emitting this warning) is deprecated.'
RUN rm -f /opt/conda/etc/profile.d/mamba.sh

RUN echo 'envs_dirs: [ ~/.conda ]' >> /opt/conda/.condarc

# XXX Uncomment this out to reproduce the issue:
#RUN conda install libmamba=2.3.0

RUN conda create -yn conda-lock conda-lock=3.0.3 \
  && conda clean --all -f -y \
  && fix-permissions "/home/$NB_USER"
ENV PATH="/home/$NB_USER/.conda/conda-lock/bin:$PATH"

COPY --chown=$NB_UID:$NB_GID environment.yml conda-lock.yml upsert-kernel-env.py test.sh /home/$NB_USER/

USER ${NB_UID}:${NB_GID}

RUN /home/$NB_USER/upsert-kernel-env.py test

CMD ["/home/jovyan/test.sh"]
