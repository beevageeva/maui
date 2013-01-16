#!/bin/bash

# Asigna un nombre al trabajo. Por defecto, es el nombre del script de trabajo PBS.
#SBATCH --job-name={{jobName}}
# Numero de nodos y de procesadores por nodo que se solicitan.
#SBATCH -N {{numNodes}}           
#SBATCH --ntasks-per-node={{procsNode}}
{% if mem %}
#SBATCH --mem-per-cpu={{mem}}
{% endif %}
# Nombre de la particion a la que se desea enviar el trabajo. 
# Las particiones disponibles son: debug
#SBATCH --partition={{queue}}
# Tiempo maximo total durante el cual el trabajo puede estar ejecutandose (horas:min:seg).
{% if walltime%}
#SBATCH --time={{walltime}}
{% endif %}
# Ruta y nombre del fichero al que se redirige la salida estandar.
#SBATCH -o {{outfile}}
# Ruta y nombre del fichero al que se redirige la salida estandar de errores.
#SBATCH -e {{errorfile}}
{% if resid %}
#SBATCH reservation={{resid}}
{% endif %}

#SBATCH --no-requeue

echo $SLURM_NODELIST > nodesinfo.txt

# Codigo correspondiente a la ejecucion de nuestro programa en particular
{{execcode}}
