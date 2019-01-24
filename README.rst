================================================================================
USGS 3DEP LiDAR Point Clouds
================================================================================


.. contents:: Contents
   :depth: 2

Project Description
--------------------------------------------------------------------------------

This AWS Public Dataset project is about processing the USGS 3DEP LiDAR point cloud data into
a form that is cloud-friendly, streamable, lossless, and convenient.

The main landing page on AWS for the project is at https://registry.opendata.aws/usgs-lidar/

Public 3DEP LiDAR data is available in two forms on AWS:

1. A `Requester Pays
   <https://docs.aws.amazon.com/AmazonS3/latest/dev/RequesterPaysBuckets.html>`__
   bucket at ``s3://usgs-lidar`` containing many of the USGS resources
   available as full-density `LASzip`_ tiles

2. A public access bucket at ``s3://usgs-lidar-public`` containing EPT resources
   mirroring many (but not all) of the resources in #1.

Entwine
................................................................................

A description of the `EPT`_ format, which is a hierarchical format arranged by
progressive level-of-detail, is contained at
https://entwine.io/entwine-point-tile.html.  EPT was chosen as the service
mechanism for this data due to its scalability potential to trillions of
points, flexibility, and its ease of use via open source infrastructure like
`PDAL`_, `LASzip`_, `Potree`_, and `Plasio.js`_.

To generate EPT datasets for your own data with Entwine, visit the `quickstart
<https://entwine.io/quickstart.html>`__ and browse the `configuration
documentation <https://entwine.io/configuration.html>`__ for more advanced
usage.

Processing
................................................................................

Data processing with `Entwine`_ was performed on AWS EC2 ``c5d.9xlarge``
instances using `S3 <https://aws.amazon.com/s3/>`__ for output storage.
Currently, there are more than 10 trillion LiDAR points available in over 950
distinct resources.

Visualization
................................................................................

The point cloud data may be visualized with `Potree`_ or
`Plasio.js`_ via the index at http://usgs.entwine.io.

Coordinate System
................................................................................

The EPT data is accessible via `EPSG:3857 <https://epsg.io/3857>`__ for ease of web usage - with PDAL the
data can be reprojected on the fly with the `reprojection filter
<https://pdal.io/stages/filters.reprojection.html>`__ which can be used in
combination with other processing pipeline stages.

The `EPT reader <https://pdal.io/stages/readers.ept.html>`__ within `PDAL`_
may also be used to select areas of data for use locally.





Resource Links
--------------------------------------------------------------------------------

* `Entwine`_
* `PDAL`_ `readers.ept`_
* `Potree`_
* `Plasio.js`_

.. _`readers.ept`: https://pdal.io/stages/readers.ept.html
.. _`Potree`: http://potree
.. _`Plasio.js`: https://github.com/hobu/plasio.js

Support
--------------------------------------------------------------------------------

Thank you to the multiple organizations that have supported the development of
the USGS 3DEP LiDAR dataset.


USACE CRREL
................................................................................

.. image:: ./images/rsgis_logo.png
    :target: http://www.erdc.usace.army.mil/Locations/CRREL.aspx
    :scale: 30%


The US Army Corps of Engineers Remote Sensing / GIS Center of Expertise at
`CRREL`_ sponsored the processing and development of the `AWS 3DEP Public Dataset`_
in multiple ways. First, it sponsored the development and continuing support of `PDAL`_ and `Entwine`_
open source software libraries, which were used to process and manage the data. Second,
it supported the processing and management of the 3DEP data to an `Entwine Point Tiles`_
public dataset.

Amazon Web Services Public Datasets Team
................................................................................

.. image:: https://d0.awsstatic.com/logos/powered-by-aws.png
    :target: https://registry.opendata.aws
    :scale: 30%

The AWS Public Datasets Team supported the effort by providing processing and
storage grants for the development of the `EPT`_ data and ongoing support by
making access to that data publicly available.


Hobu, Inc.
................................................................................

.. image:: ./images/hobu-logo-2C-white.png
    :target: https://hobu.co
    :scale: 30%

`Connor Manning`_ from `Hobu, Inc.`_ constructed the 3DEP EPT resources with
cloud processing and management tools from `Hobu, Inc.`_.

.. _`Connor Manning`: http://github.com/connormanning/
.. _`Hobu, Inc.`: https://hobu.co
.. _`Entwine`: https://entwine.io
.. _`PDAL`: https://pdal.io
.. _`CRREL`: https://www.erdc.usace.army.mil/Locations/CRREL.aspx

.. _`Entwine Point Tiles`: https://entwine.io/entwine-point-tile.html
.. _`EPT`: https://entwine.io/entwine-point-tile.html
.. _`LASzip`: https://laszip.org

.. _`AWS 3DEP Public Dataset`: https://registry.opendata.aws/usgs-lidar/
