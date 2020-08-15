## AUTHOR : RADHA KRISHNA KAVULURU . K

## Context : This has utilities to preprocess shapefiles are rasters for processing
import gdal,ogr,osr
import os
import numpy as np


def ClipShapeWithRaster(shape_file,mask_file,raster_file,output_file):
    
    # open raster and obtain extent and properties
    data = gdal.Open(raster_file, gdal.GA_ReadOnly)
    geo_transform = data.GetGeoTransform() #[xc,xres,xskew,yc,yskew,yres]
    xres=geo_transform[1]
    yres=geo_transform[5]
    top_left=[geo_transform[0],geo_transform[3]]
    raster_prj = osr.SpatialReference()
    raster_prj.ImportFromWkt(data.GetProjectionRef())
 
    # open shapefile 
    shapes=ogr.Open(shape_file)
    shp_layer=shapes.GetLayer()
    shape_prj=shp_layer.GetSpatialRef()
    #create a co-ordinateTrans
    coordTrans = osr.CoordinateTransformation(raster_prj,shape_prj)
    revTrans=osr.CoordinateTransformation(shape_prj,raster_prj)
    #get the raster boundary
    
    #all rasters are rectangles.Can interpolate from geo_transform and length and width.
    rows=data.RasterYSize
    cols=data.RasterXSize
    top_right=[top_left[0]+(xres*cols),top_left[1]]
    bottom_right=[top_left[0]+(xres*cols),top_left[1]+(yres*rows)]
    bottom_left=[top_left[0],top_left[1]+(yres*rows)]
    ring = ogr.Geometry(ogr.wkbLinearRing)
    boundary=[
        top_left,top_right,bottom_right,bottom_left
    ]
    for point in boundary:
        ring.AddPoint(*point)
    #close ring
    ring.AddPoint(*top_left)
    ring.Transform(coordTrans)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    ## Clipped Shapefile... Maybe??? 
    driverName = "ESRI Shapefile"
    driver = ogr.GetDriverByName(driverName)
    #------------------------------------------------
    #temporary layer for CLIP operation of ogr
    temp_ds= driver.CreateDataSource( f"/vsimem/clip.shp" )
    temp_layer=temp_ds.CreateLayer('clip', geom_type=ogr.wkbPolygon)
    feature = ogr.Feature(temp_layer.GetLayerDefn())
    feature.SetGeometry(poly)
    temp_layer.CreateFeature(feature)
    feature.Destroy()
    #transfor shp_layer to raster crs
    
    #----------------------------------------------------------
    out_temp_DataSource = driver.CreateDataSource("/vsimem/intermediate.shp" )
    out_temp_Layer = out_temp_DataSource.CreateLayer('Buildings', geom_type=ogr.wkbMultiPolygon)
    outDataSource = driver.CreateDataSource(output_file )
    outLayer = outDataSource.CreateLayer('Buildings',raster_prj, geom_type=ogr.wkbMultiPolygon)
    outLayerDefn=outLayer.GetLayerDefn()
    ogr.Layer.Clip(shp_layer, temp_layer , out_temp_Layer)
    print(f"Clipped layer , output has feature count = {out_temp_Layer.GetFeatureCount()}")
    # loop through the input features
    inFeature = out_temp_Layer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(revTrans)
        # create a new feature

        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # dereference the features and get the next input feature
        outFeature = None
        inFeature = out_temp_Layer.GetNextFeature()
    temp_ds.Destroy()
    outDataSource.Destroy()
    out_temp_DataSource.Destroy()
    data=None

def RasterizeShapeMatchRaster(shape_file,raster_file,output_file):
    # open raster and obtain extent and properties
    data = gdal.Open(raster_file ,gdal.GA_ReadOnly)
    geo_transform = data.GetGeoTransform()
    #source_layer = data.GetLayer()
    x_min = geo_transform[0]
    y_max = geo_transform[3]
    x_max = x_min + geo_transform[1] * data.RasterXSize
    y_min = y_max + geo_transform[5] * data.RasterYSize
    x_len = data.RasterXSize
    y_len = data.RasterYSize
    mb_v = ogr.Open(shape_file)
    mb_l = mb_v.GetLayer()
    pixel_width = geo_transform[1]
    target_ds = gdal.GetDriverByName('GTiff').Create(output_file, x_len, y_len, 1, gdal.GDT_Byte)
    target_ds.SetGeoTransform(geo_transform)
    band = target_ds.GetRasterBand(1)
    NoData_value = -999999
    band.SetNoDataValue(NoData_value)
    target_ds.SetProjection(data.GetProjectionRef())
    band.FlushCache()
    gdal.RasterizeLayer(target_ds, [1], mb_l,burn_values=[255])

    target_ds = None
def StackBands(bands_list,vrtout):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic',separate=True)
    my_vrt = gdal.BuildVRT(vrtout,bands_list, options=vrt_options)
    my_vrt = None
def CheckEmpty(tile):
        bands,rows,cols=tile.shape
        tile=tile.reshape((rows,cols,bands))
        y,x,b=np.where(tile==[0,0,0])
        if(len(y)==0):
            return False
        else:
            return True
def NormalizeTile(tile,scalemax=255):
    tile=(tile-tile.min())/(tile.max()-tile.min())
    return tile*scalemax
def TileRasterLabels(data_raster,label_raster,outdir,tile_size=256):
    #blocks raster1 zeropadded areas  and prepares supervised datasets
    
    
    #raster1 and raster2 should be equal width and height
    data1 = gdal.Open(data_raster,gdal.GA_ReadOnly)
    data2 = gdal.Open(label_raster,gdal.GA_ReadOnly)
    bandcount=data1.RasterCount
    x_len = data1.RasterXSize
    y_len = data1.RasterYSize
    grids_x=int(x_len/tile_size)
    grids_y=int(y_len/tile_size)
    print(f"total number of tiles possible={grids_x*grids_y}")
    labels_dir=os.path.join(outdir,'labels')
    data_dir=os.path.join(outdir,'data')
    os.makedirs(labels_dir,exist_ok=True)
    os.makedirs(data_dir,exist_ok=True)
    geotransform=data1.GetGeoTransform()
    for xgrid in range(0,grids_x):
        for ygrid in range(0,grids_y):
            #print(xgrid,ygrid)
            xcount=tile_size
            ycount=tile_size
            xoff=xgrid*tile_size
            yoff=ygrid*tile_size
            if(xoff+xcount>x_len):
                break 
            if(yoff+ycount>y_len):
                break
            data_array=data1.ReadAsArray(xoff,yoff,xcount,ycount) #shape=(bands,rows,cols)
            if(CheckEmpty(data_array)):
                continue
            label_array=data2.ReadAsArray(xoff,yoff,xcount,ycount)
            data_array=NormalizeTile(data_array)
            label_array=NormalizeTile(label_array)
            data_ds = gdal.GetDriverByName('GTiff').Create(f"{data_dir}/x{xgrid}_y{ygrid}.tif", tile_size,tile_size, bandcount, gdal.GDT_Byte)
            label_ds = gdal.GetDriverByName('GTiff').Create(f"{labels_dir}/x{xgrid}_y{ygrid}.tif", tile_size, tile_size, 1, gdal.GDT_Byte)
            for band in range(0,bandcount):
                outband = data_ds.GetRasterBand(band+1)
                outband.WriteArray(data_array[band])
            
            new_geotransform=list(geotransform)
            new_geotransform[0]=new_geotransform[0]+(xoff*new_geotransform[1])
            new_geotransform[3]=new_geotransform[3]+(yoff*new_geotransform[5])
            data_ds.SetProjection(data1.GetProjectionRef())
            data_ds.SetGeoTransform(new_geotransform)
            label_ds.SetProjection(data1.GetProjectionRef())
            label_ds.SetGeoTransform(new_geotransform)
            outband.FlushCache()
            labelband=label_ds.GetRasterBand(1)
            labelband.WriteArray(label_array)
            labelband.FlushCache()
            data_ds=None 
            label_ds=None
if(__name__=="__main__"):

    raster_file = "/home/radhakrishna/Desktop/projects/data/S2A_MSIL1C_20200428T050701_N0209_R019_T43QHV_20200428T081746.SAFE/GRANULE/L1C_T43QHV_A025327_20200428T051509/IMG_DATA/T43QHV_20200428T050701_B02.jp2"
    mask_file = "/home/radhakrishna/Desktop/projects/deep_learning/sat2map/tests/shapefiles/test.shp"
    shape_file="/home/radhakrishna/Desktop/projects/data/india_shapes/gis_osm_buildings_a_free_1.shp"
    clip_shape_file = "/home/radhakrishna/Desktop/projects/deep_learning/sat2map/tests/shapefiles/output.shp"
    label_file="/home/radhakrishna/Desktop/projects/deep_learning/sat2map/tests/raster/label.tiff"
    bands_list=[
        '/home/radhakrishna/Desktop/projects/data/S2A_MSIL1C_20200428T050701_N0209_R019_T43QHV_20200428T081746.SAFE/GRANULE/L1C_T43QHV_A025327_20200428T051509/IMG_DATA/T43QHV_20200428T050701_B02.jp2',
        '/home/radhakrishna/Desktop/projects/data/S2A_MSIL1C_20200428T050701_N0209_R019_T43QHV_20200428T081746.SAFE/GRANULE/L1C_T43QHV_A025327_20200428T051509/IMG_DATA/T43QHV_20200428T050701_B03.jp2',
        '/home/radhakrishna/Desktop/projects/data/S2A_MSIL1C_20200428T050701_N0209_R019_T43QHV_20200428T081746.SAFE/GRANULE/L1C_T43QHV_A025327_20200428T051509/IMG_DATA/T43QHV_20200428T050701_B04.jp2'
    ]
    vrtout='tests/raster/stack.vrt'
    outdir='/home/radhakrishna/Desktop/projects/deep_learning/sat2map/tests/raster/1_out/'
    #ClipShapeWithRaster(shape_file,mask_file,raster_file,clip_shape_file)
    RasterizeShapeMatchRaster(clip_shape_file,raster_file,label_file)
    #StackBands(bands_list,vrtout)
    TileRasterLabels(vrtout,label_file,outdir,tile_size=256)

