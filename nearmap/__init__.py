####################################
#   File name: __init__.py
#   About: The Nearmap API for Python
#   Authors: Geoff Taylor | Sr Solution Architect | Nearmap
#            Connor Tluck | Solutions Engineer | Nearmap
#   Date created: 7/7/2021
#   Last update: 9/17/2021
#   Python Version: 3.6+
####################################

import nearmap._api as _api


class NEARMAP(object):
    """
        .. _NEARMAP:

        A NEARMAP is representative of the main access point to a users API calls.

        ================    ===============================================================
        **Argument**        **Description**
        ----------------    ---------------------------------------------------------------
        api_key             Your Nearmap API Key. More info: https://docs.nearmap.com/display/ND/Managing+API+Keys
        ----------------    ---------------------------------------------------------------

        .. code-block:: python

            # Usage Example: Connect to Nearmap using API Key

            nearmap = NEARMAP()
    """

    base_url = "https://api.nearmap.com/"
    api_key = None

    def __init__(self, api_key=None):
        if api_key is None:
            raise Exception("error: API Key not detected")
        self.api_key = api_key

    ####################
    # Download Features
    ###################

    # Coming Soon! In Development

    ###############
    #  NEARMAP AI
    #############
    def aiFeaturesV4(self, polygon, since=None, until=None, packs=None, out_format="json", lat_lon_direction="yx",
                     surveyResourceID=None):
        """
        Function retrieves AI Feature tiles for a specified location. Use this API to access vectorized
        features detected using AI with optional date control.
        More Info: https://docs.nearmap.com/display/ND/AI+Feature+API

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        polygon             Required string or list of lon/lat coords in WGS84 (EPSG : 4326)
                            Example: "lon1,lat1,lon2,lat2,..." -or [lon1,lat1,lon2,lat2,...]
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the ai data (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve ai data since this
                                date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve ai data since 5
                                months ago.
                            Notes:
                                -If specified, the since parameter controls the earliest ai data that is
                                returned & ikf there are multiple captures after the date specified by the since
                                parameter, the latest ai data is returned.
                                -If neither since nor until are specified, the request returns the latest ai
                                data.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the ai data (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. dis to retrieve ai data until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve ai data until 5
                                months ago.
                            Notes:
                                -If specified, and ai data at that location at that date exists, the request
                                returns the data.
                                -If specified, and ai data at that location at that date does not exist, the
                                request returns asi data of the next available date before the specified date.
                                -If neither since nor until are specified, the request returns the latest ai
                                data.
        ---------------     --------------------------------------------------------------------
        packs               Optional string.    Input the name or list of names for the AI packs you want to download.
                            Example: "Building Footprints"

                            If you are unsure what AI Packs you have access to with your nearmap subscription
                            use the nearmap.aiPacks() function to list them.

                            More Information on AI Packs: https://docs.nearmap.com/display/ND/AI+Packs
        ---------------     --------------------------------------------------------------------
        out_format          Optional string.    Output format for returning AI Features. If not specified JSON will be
                            returned by default.
                            The available values are:
                                "json" - returns a json object (This is the default)
                                "text" - returns a text object
                                "pandas" - returns a pandas dataframe object
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ---------------     --------------------------------------------------------------------
        surveyResourceID    placeholder for later use.... of no current usage value
        ===============     ====================================================================

        :return: json, text, or pandas dataframe object

        """
        return _api.aiFeaturesV4(self.base_url, self.api_key, polygon, since, until, packs, out_format,
                                 lat_lon_direction, surveyResourceID)

    def aiClassesV4(self, out_format="json"):
        """
        The classes.json endpoint is used to retrieve information about all the Feature Classes you have access to with
        your AI Packs. All the features (polygons) returned by the features.json endpoint have both an individual uuid
        for unique identification, and a feature class, which also has a uuid . The feature class (such as "Building")
        allows you to code specific patterns of behaviour in your application when features of that specific type are
        returned – whether to control z order and styling for visualisation purposes, or to inspect and use the metadata
        as part of your workflow.
        More Info: https://docs.nearmap.com/display/ND/AI+Feature+API

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        out_format          Optional string.  The out_format flag species the output format to return the data as.
                            The available values are:
                                json - returns a json object (This is the default)
                                text - returns a text object
                                pandas - returns a pandas dataframe object
        ===============     ====================================================================

        :return: json, text, or pandas dataframe object

        """
        return _api.aiClassesV4(self.base_url, self.api_key, out_format)

    def aiPacksV4(self, out_format="json"):
        """
        The packs.json endpoint is used to show which packs are available on the user's subscription and provides a
        richer and more complex data structure than the more simple classes.json endpoint.
        More Info: https://docs.nearmap.com/display/ND/AI+Feature+API

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        out_format              Optional string.  The out_format flag species the output formt to return the data as.
                            The available values are:
                                json - returns a json object (This is the default)
                                text - returns a text object
                                pandas - returns a pandas dataframe object
        ===============     ====================================================================

        :return: json, text, or pandas dataframe object

        """
        return _api.aiPacksV4(self.base_url, self.api_key, out_format)

    #####################
    #  NEARMAP Coverage
    ###################

    def polyV2(self, polygon, since=None, until=None, limit=20, offset=None, fields=None, sort=None, overlap=None,
               include=None, exclude=None, lat_lon_direction="yx"):
        """
        Use this API for querying dates and other attributes for a small geographic area. For example, in interactive
        web applications.
        More Info: https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-RetrieveMetadataforaGivenPolygon

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        polygon             Required string or list of lon/lat coords in WGS84 (EPSG : 4326)
                            Example: "lon1,lat1,lon2,lat2,..." -or [lon1,lat1,lon2,lat2,...]
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys since this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys since 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys until 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        limit               Optional integer.   The limit of the total number of surveys returned. The default value is
                            20. The surveys are returned from the most recent to the least recent survey.

        ---------------     --------------------------------------------------------------------
        offset              Optional integer.   The offset of the first survey to be displayed. With no offset, the
                            first survey to be displayed is the most recent one. If the offset is 3 for example, the
                            first survey to be displayed is the 4th recent one.
        ---------------     --------------------------------------------------------------------
        fields              Optional string.    This is a comma-separated list of field names that will appear in the
                            response.
                            The id field will always be among the returned fields, even if not specified.
                            If this parameter is not used in the URL request, then all the fields are returned.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -resources
                                -timezone
                                -utcOffset
                            Note: the fields values are case sensitive.
        ---------------     --------------------------------------------------------------------
        sort                Optional string.    The field by which to sort the surveys.
                            Only one field can be specified.
                            If this parameter is not used in the URL request, then the surveys are sorted by captureDate
                            in descending order.
                            To sort in ascending order, pass the field name, e.g sort=lastPhotoTime. This will sort the
                            surveys according to the lastPhotoTime from earliest to latest.
                            To sort in descending order, pass the field name with the "-" prefix, e.g. sort=-pixelSize.
                            This will sort the surveys according to the pixelSize from the largest to the smallest.
                            If you sort by location, the following are the precedence rules for comparing location
                            objects:
                                -country
                                -state
                                -region
                            For example, "NZ, MWT, PalmerstonNorth" will come after "AU, NSW, Williamstown" if sorted in
                            ascending order.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -timezone
                                -utcOffset
        ---------------     --------------------------------------------------------------------
        overlaps            Optional string. Controls whether surveys that partially cover the requested polygon are
                            returned.
                            The possible values are as follows:
                                -all (default) - all surveys that partially or fully overlap with requested polygon are
                                returned
                                -full - only the surveys that fully cover the requested polygon are returned
        ---------------     --------------------------------------------------------------------
        include             Optional string.    Filters surveys so that only those tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        exclude             Optional string.    Filters surveys so that only those not tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ===============     ====================================================================

        :return: json

        """
        return _api.polyV2(self.base_url, self.api_key, polygon, since, until, limit, offset, fields, sort, overlap,
                           include, exclude, lat_lon_direction)

    def pointV2(self, point, since=None, until=None, limit=20, offset=None, fields=None, sort=None, include=None,
                exclude=None, lat_lon_direction="yx"):
        """
        Use this API for querying dates and other attributes for a point. For example, checking if there is Nearmap
        coverage at a geocoded address.
        More Info: https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-RetrieveMetadataforaGivenPoint

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        point               Required string or list containing an individual lon/lat coord in WGS84 (EPSG : 4326)
                            This is the point for which the surveys are retrieved. The point is the longitude and
                            latitude of the location on which to center the image, in the format LONG,LAT.
                            For example, "-122.008946,37.334849" -or- [-122.008946,37.334849]
                            Note: the LONG comes before the LAT.
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys since this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys since 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys until 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        limit               Optional integer.   The limit of the total number of surveys returned. The default value is
                            20. The surveys are returned from the most recent to the least recent survey.
        ---------------     --------------------------------------------------------------------
        offset              Optional integer.   The offset of the first survey to be displayed. With no offset, the
                            first survey to be displayed is the most recent one. If the offset is 3 for example, the
                            first survey to be displayed is the 4th recent one.
        ---------------     --------------------------------------------------------------------
        fields              Optional string.    This is a comma-separated list of field names that will appear in the
                            response.
                            The id field will always be among the returned fields, even if not specified.
                            If this parameter is not used in the URL request, then all the fields are returned.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -resources
                                -timezone
                                -utcOffset
                            Note: the fields values are case sensitive.
        ---------------     --------------------------------------------------------------------
        sort                Optional string.    The field by which to sort the surveys.
                            Only one field can be specified.
                            If this parameter is not used in the URL request, then the surveys are sorted by captureDate
                            in descending order.
                            To sort in ascending order, pass the field name, e.g sort=lastPhotoTime. This will sort the
                            surveys according to the lastPhotoTime from earliest to latest.
                            To sort in descending order, pass the field name with the "-" prefix, e.g. sort=-pixelSize.
                            This will sort the surveys according to the pixelSize from the largest to the smallest.
                            If you sort by location, the following are the precedence rules for comparing location
                            objects:
                                -country
                                -state
                                -region
                            For example, "NZ, MWT, PalmerstonNorth" will come after "AU, NSW, Williamstown" if sorted in
                            ascending order.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -timezone
                                -utcOffset
        ---------------     --------------------------------------------------------------------
        include             Optional string.    Filters surveys so that only those tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        exclude             Optional string.    Filters surveys so that only those not tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ===============     ====================================================================

        :return: json

        """
        return _api.pointV2(self.base_url, self.api_key, point, since, until, limit, offset, fields, sort, include,
                            exclude, lat_lon_direction)

    def coordV2(self, z, x, y, since=None, until=None, limit=20, offset=None, fields=None, sort=None, include=None,
                exclude=None):
        """
        Use this API for querying dates and other attributes for a Google x/y/z tile coordinate. Provided for legacy
        compatibility reasons. Equivalent to the /`poly` request with the extent of the particular tile.
        More Info: https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-RetrieveMetadataforaGivenTileCoordinate

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        z                   Required integer.   The zoom level. The highest resolution is typically 21.
                            Uses the Google Maps Tile Coordinates.
                            https://developers.google.com/maps/documentation/javascript/coordinates
                            Example: 16
        ---------------     --------------------------------------------------------------------
        x                   Required integer.   The X tile coordinate for which the surveys are retrieved (column).
                            Uses the Google Maps Tile Coordinates.
                            https://developers.google.com/maps/documentation/javascript/coordinates
                            Example: 57999
        ---------------     --------------------------------------------------------------------
        y                   Required integer.   The Y tile coordinate for which the surveys are retrieved (row).
                            Uses the Uses the Google Maps Tile Coordinates.
                            https://developers.google.com/maps/documentation/javascript/coordinates
                            Example: 39561
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys since this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys since 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys until 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        limit               Optional integer.   The limit of the total number of surveys returned. The default value is
                            20. The surveys are returned from the most recent to the least recent survey.
        ---------------     --------------------------------------------------------------------
        offset              Optional integer.   The offset of the first survey to be displayed. With no offset, the
                            first survey to be displayed is the most recent one. If the offset is 3 for example, the
                            first survey to be displayed is the 4th recent one.
        ---------------     --------------------------------------------------------------------
        fields              Optional string.    This is a comma-separated list of field names that will appear in the
                            response.
                            The id field will always be among the returned fields, even if not specified.
                            If this parameter is not used in the URL request, then all the fields are returned.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -resources
                                -timezone
                                -utcOffset
                            Note: the fields values are case sensitive.
        ---------------     --------------------------------------------------------------------
        sort                Optional string.    The field by which to sort the surveys.
                            Only one field can be specified.
                            If this parameter is not used in the URL request, then the surveys are sorted by captureDate
                            in descending order.
                            To sort in ascending order, pass the field name, e.g sort=lastPhotoTime. This will sort the
                            surveys according to the lastPhotoTime from earliest to latest.
                            To sort in descending order, pass the field name with the "-" prefix, e.g. sort=-pixelSize.
                            This will sort the surveys according to the pixelSize from the largest to the smallest.
                            If you sort by location, the following are the precedence rules for comparing location
                            objects:
                                -country
                                -state
                                -region
                            For example, "NZ, MWT, PalmerstonNorth" will come after "AU, NSW, Williamstown" if sorted in
                            ascending order.
                            The available values are:
                                -captureDate
                                -firstPhotoTime
                                -id
                                -lastPhotoTime
                                -location
                                -onlineTime
                                -pixelSize
                                -timezone
                                -utcOffset
        ---------------     --------------------------------------------------------------------
        include             Optional string.    Filters surveys so that only those tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        exclude             Optional string.    Filters surveys so that only those not tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ===============     ====================================================================

        :return: json

        """
        return _api.coordV2(self.base_url, self.api_key, z, x, y, since, until, limit, offset, fields, sort, include,
                            exclude)

    def surveyV2(self, polygon, fileFormat="geojson", since=None, until=None, limit=20, offset=None, resources=None,
                 overlap=None, include=None, exclude=None, lat_lon_direction="yx"):
        """
        Use this API for downloading coverage polygons to cross reference against your own spatial database.
        For example, to check which of your assets are contained within a particular survey.
        More Info: https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-RetrieveContentBoundariesforaGivenPolygon

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        polygon             Required string or list of lon/lat coords in WGS84 (EPSG : 4326)
                            Example: "lon1,lat1,lon2,lat2,..." -or [lon1,lat1,lon2,lat2,...]
        ---------------     --------------------------------------------------------------------
        fileFormat          Optional string.    The response file format. The supported file format is geojson.
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys since this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys since 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the surveys (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve surveys until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve surveys until 5 months ago.
                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        limit               Optional integer.   The limit of the total number of surveys returned. The default value is
                            20. The surveys are returned from the most recent to the least recent survey.
        ---------------     --------------------------------------------------------------------
        offset              Optional integer.   The offset of the first survey to be displayed. With no offset, the
                            first survey to be displayed is the most recent one. If the offset is 3 for example, the
                            first survey to be displayed is the 4th recent one.
        ---------------     --------------------------------------------------------------------
        resources           Optional string.    A comma-separated list of resource classes to include in the response.
                            The resource classes are returned in the form of "resourceClass:type" where ":type" is
                            optional and represents all types of a resource class if not present.
                            The resources possible values are:
                                -tiles:Vert
                                -tiles:North
                                -tiles:East
                                -tiles:South
                                -tiles:West
                            If not specified then all resources are returned.
        ---------------     --------------------------------------------------------------------
        overlap             Optional string.    Controls whether surveys that partially cover the requested polygon are
                            returned. The possible values are as follows:
                                -all (default) - all surveys that partially or fully overlap with requested polygon are
                                returned
                                -full - only the surveys that fully cover the requested polygon are returned
        ---------------     --------------------------------------------------------------------
        include             Optional string.    Filters surveys so that only those tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        exclude             Optional string.    Filters surveys so that only those not tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                -type:name, e.g. disaster:hurricane
                                -type, e.g. disaster
                                -name, e.g. hurricane
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ===============     ====================================================================

        :return: json

        """
        return _api.surveyV2(self.base_url, self.api_key, polygon, fileFormat, since, until, limit, offset, resources,
                             overlap, include, exclude, lat_lon_direction)

    def coverageV2(self, fileFormat="geojson", types=None):
        """
        Use this API for visualisation of aggregated Nearmap coverage. For example, to create an interactive map that
        shows where there is Nearmap coverage.
        More Info: https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-RetrieveAggregatedCoverageBoundaries

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        fileFormat          Optional String: The response file format. The supported file format is geojson.
        ---------------     --------------------------------------------------------------------
        types               Optional string:    Comma-separated list of categories to include in the response.
                            The types possible values are:
                                -Vertical
                                -Oblique
                                -3D
                            If not specified, then all categories are returned.
        ===============     ====================================================================

        :return: json

        """
        return _api.coverageV2(self.base_url, self.api_key, fileFormat, types)

    ###############################
    # NEARMAP DSM & TrueOrtho API
    #############################

    def coverageStaticMapV2(self, point, radius, resources=None, overlap=None, since=None, until=None, fields=None,
                            limit=100, offset=None, lat_lon_direction="yx"):
        """
        This function provides the details on the available coverage for the requested area. The area is given bounding
        box, defined by a point and a distance from the point. This is separate from the existing Coverage APIs as the
        coverage call creates a transaction token that should be used to retrieve the image.

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        point               Required string or list. The point for which the surveys are retrieved. The point is the
                            longitude and latitude of the location on which to centre the image, in the format LONG,LAT.
                            For example, "-74.044831,40.689669" -or- [-74.044831, 40.689669]
                            Note:
                                LONG comes before LAT
        ---------------     --------------------------------------------------------------------
        radius              Required integer. Distance from the point in metres. Used in conjunction with point to
                            define a bounding box(not a circle). Radius range between 1-100.
        ---------------     --------------------------------------------------------------------
        resources           Required string. Comma separated list of resource types indicating the survey resources to
                            return in the response.
                            This can be any or all of:
                                "DetailDsm"
                                "TrueOrtho"
                                "Vert"
                            Example: "DetailDsm,TrueOrtho,Vert"
        ---------------     --------------------------------------------------------------------
        overlap             Optional string. Whether or not to return metadata for imagery that only partially
                            intersects the requested area. Default is to return all, such that surveys that only
                            partially intersect the AOI will still be returned. If full is specified, then only surveys
                            completely within the given AOI are included.
                            Options include:
                                "full"
                                "all"
        ---------------     --------------------------------------------------------------------
        since               Optional string. The first day from which to retrieve the surveys (inclusive).
                            The two possible formats are:

                                For a specific date: "YYYY-MM-DD"
                                    E.G. "2015-10-31" to retrieve surveys since this date

                                For a relative date: "xxY", "xxM" or "xxD"
                                    E.G. "5M" to retrieve surveys since 5 months ago.

                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        until               Optional string. The last day from which to retrieve the surveys (inclusive).

                            The two possible formats are:

                                For specific date: "YYYY-MM-DD"
                                    E.G. "2015-10-31" to retrieve surveys until this date
                                For a relative date: "xxY", "xxM", or "xxD"
                                    E.G. "5M" to retrieve surveys until 5 months ago

                            The since and until parameters are used to further restrict the surveys that are returned.
        ---------------     --------------------------------------------------------------------
        fields              Optional string. Comma separated list of field names that will appear in the response. The
                            id field will always be among the returned fields, even if it is not specified. If this
                            parameter is not present, then all fields are returned.

                            This can be any or all of:
                                "id"
                                "captureDate"
                                "firstPhotoTime"
                                "lastPhotoTime"
                                "pixelSizes"

                            Example: "id,captureDate,firstPhotoTime,lastPhotoTime,pixelSizes"

                            Note: the fields values are case sensitive.
        ---------------     --------------------------------------------------------------------
        limit               Optional integer. Limit the number of surveys in the result.

                            Default is 100, Maximum is 1000.
        ---------------     --------------------------------------------------------------------
        offset              Optional integer. The offset of the first survey to be displayed.

                            With no offset, the first survey to be displayed is the most recent one.
                            If the offset is 3', the first survey to be displayed will be the 4th most recent survey.
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ===============     ====================================================================

        :return: json

        """
        return _api.coverageStaticMapV2(self.base_url, self.api_key, point, radius, resources, overlap, since, until,
                                        fields, limit, offset, lat_lon_direction)

    def imageStaticMapV2(self, surveyID, image_type, file_format, point, radius, size, transactionToken, out_image,
                         lat_lon_direction="yx"):
        """
        Function returns raster content based on the location, content type and output format. The same request with
        different content types will return an image of the same area.

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        surveyID            Required string. Identifier of the survey to retrieve content for as obtained from the
                            coverage response. This will correspond to a specific date.
        ---------------     --------------------------------------------------------------------
        image_type          Required string. Type of raster content to return. This corresponds to the requested types
                            in the coverage end point.
                            Available values:
                                DetailDsm - for Digital Surface Model Raster
                                TrueOrtho - for On-Nadir Ortho Raster
                                Vert - for traditional Ortho Raster
        ---------------     --------------------------------------------------------------------
        file_format         Requires string. File format of the resulting raster image.
                            Available values:
                                -tif
                                -jpg
                                -png
                                -jgw
                                -pgw
                                -tfw
        ---------------     --------------------------------------------------------------------
        point               Required string or list containing coordinate pair. The point for which the surveys are
                            retrieved. The point is the longitude and latitude of the location on which to center the
                            image, in the format LONG,LAT.
                            Example : "-73.557105,40.806290" -or- [-73.557105,40.806290]
        ---------------     --------------------------------------------------------------------
        radius              Required Integer Distance from the point in metres. Used in conjunction with point to define
                            a bounding box (not a circle). Radius range between 1 - 100
                            Example: 100
        --------------      --------------------------------------------------------------------
        size                Required string. Size of the resultant image in pixels. It is the responsibility of the
                            caller to maintain the aspect ratio of the requested image. The format is {width}x{height},
                            however only equal width and height values are currently supported. Maximum image size is
                            "5000x5000".
                            Example : 1024x1024
        ---------------     --------------------------------------------------------------------
        transactionToken    Required string. Transaction token to use in an image request. This token is returned in the
                            staticmap coverage response and contains the authentication information for the request.
                            Multiple image requests made using the same transaction tokens do not incur additional usage
                            costs within 30 days since the coverage call was made.
        ---------------     --------------------------------------------------------------------
        out_image           Required string.  The URL to the service or string "bytes" for streaming
        ---------------     --------------------------------------------------------------------
        lat_lon_direction   Optional string.  Reverses the ordering of the default point input parameter from lon/lat
                            to lat/lon coords to support US and other nations using this ordering.
                            Usage: "xy" for US, "yx" for other
        ===============     ====================================================================

        :return: out_image or bytes

        """
        return _api.imageStaticMapV2(self.base_url, self.api_key, surveyID, image_type, file_format, point, radius,
                                     size, transactionToken, out_image, lat_lon_direction)

    ##################
    #  NEARMAP Tiles
    ################

    def tileV3(self, tileResourceType, z, x, y, out_format, out_image, tertiary=None, since=None, until=None,
               mosaic=None, include=None, exclude=None):
        """
        Function retrieves vertical or panorama tiles for a specified location. Use this API to add a Nearmap basemap
        to your application, with optional date control.

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        tileResourceType    Required string.    The resource type for the requested tiles.
                            The available values are:
                                Vert - for vertical imagery
                                North - for North panorama imagery
                                South - for South panorama imagery
                                East - for East panorama imagery
                                West - for West panorama imagery
                                Note: the tileResourceType values are case sensitive.
        ---------------     --------------------------------------------------------------------
        z                   Required integer.   The zoom level. The highest resolution is typically 21.
                            uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        x                   Required integer.   The X tile coordinate (column).
                            Uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        y                   Required integer.   The Y tile coordinate (row).
                            Uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        out_format          Required string. The format of the tile output.
                            The available values are:
                                jpg - always JPEG
                                png - always PNG
                                img - JPEG by default, PNG when the tile is partial
                                Note that imagery is stored on Nearmap's servers as JPEG, so switching to PNG
                                does not result in improvement in quality, however it will increase the size of
                                the response.
        ---------------     --------------------------------------------------------------------
        tertiary            Optional string.    The tertiary map to return when a Nearmap tile is not found.
                            The available values are:
                                none (default) - no tertiary imagery in the background
                                satellite - use our current tertiary backdrop
                            Note: returned tiles will always be blended with tiles from another survey.
                            Tertiary tiles will only be blended when tertiary parameter is not 'none'.
        ---------------     --------------------------------------------------------------------
        since               Optional string.    The first day from which to retrieve the tiles (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. 2015-10-31 to retrieve imagery since this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve imagery since 5 months ago.
                            Notes:
                                -If specified, the since parameter controls the earliest imagery that is returned.
                                & If there are multiple captures after the date specified by the since parameter, the
                                latest imagery is returned.
                                -If the mosaic parameter is set to earliest, the imagery on or after the date specified
                                by the since parameter is returned.
                                -If neither since nor until are specified, the request returns the latest imagery.
        ---------------     --------------------------------------------------------------------
        until               Optional string.    The last day from which to retrieve the tiles (inclusive).
                            The two possible formats are:
                                -For a specific date: YYYY-MM-DD, e.g. dis to retrieve imagery until this date.
                                -For a relative date: xxY, xxM, or xxD, e.g. 5M to retrieve imagery until 5 months ago.
                            Notes:
                                -If specified, and imagery at that location at that date exists, the request returns the
                                imagery.
                                -If specified, and imagery at that location at that date does not exist, the request
                                returns imagery of the next available date before the specified date.
                                -If neither since nor until are specified, the request returns the latest imagery.
        ---------------     --------------------------------------------------------------------
        mosaic              Optional string.    Specifies the order in which the surveys covering the specified area are
                            prioritised.
                            The available values are:
                                latest - the imagery with the later capture date is prioritised
                                earliest - imagery with the earlier capture date is prioritised
                            If the mosaic parameter is not specified, the imagery with the later capture date is
                            prioritised.
                            To return imagery on or after a specified date, use mosaic=earliest in combination with the
                            since parameter.
        ---------------     --------------------------------------------------------------------
        include             Optional string.    Filters surveys so that only those tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                type:name, e.g. disaster:hurricane
                                type, e.g. disaster
                                name, e.g. hurricane
                            Refer to Coverage API - Filter Surveys for further detail on tags.
                            https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-FilterSurveys
        ---------------     --------------------------------------------------------------------
        exclude             Optional string.    Filters surveys so that only those not tagged with the type and name
                            specified are returned.
                            Tags are a type:name combination. You can also filter on type and name separately. By comma
                            separating you can include multiple tags, types and/or names.
                                type:name, e.g. disaster:hurricane
                                type, e.g. disaster
                                name, e.g. hurricane
                            Refer to Coverage API - Filter Surveys for further detail on tags.
                            https://docs.nearmap.com/display/ND/Coverage+API#CoverageAPI-FilterSurveys
        ---------------     --------------------------------------------------------------------
        out_image           Required string.  The output fil path or string "bytes" for streaming
        ===============     ====================================================================

        :return: out_image or bytes

        """
        return _api.tileV3(self.base_url, self.api_key, tileResourceType, z, x, y, out_format, out_image, tertiary,
                           since, until, mosaic, include, exclude)

    def tileSurveyV3(self, surveyid, contentType, z, x, y, out_format, out_image):
        """
        Function retrieves vertical or panorama tiles of a specified survey for a specified location.
        Use this method to retrieve imagery for a single survey

        ===============     ====================================================================
        **Argument**        **Description**
        ---------------     --------------------------------------------------------------------
        surveyid            Required string.  The survey ID in the format of UUID. Only tiles of
                            the specified survey will be returned. You can use the ID from the
                            survey object returned by the Coverage API:
                            - https://docs.nearmap.com/display/ND/Coverage+API
        ---------------     --------------------------------------------------------------------
        contentType         Required string.    The content type for the requested tiles.
                            The available values are:
                                Vert - for vertical imagery
                                North - for North panorama imagery
                                South - for South panorama imagery
                                East - for East panorama imagery
                                West - for West panorama imagery
                            Note: the tileResourceType values are case sensitive.
        ---------------     --------------------------------------------------------------------
        z                   Required integer.   The zoom level. The highest resolution is typically 21.
                            uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        x                   Required integer.   The X tile coordinate (column).
                            Uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        y                   Required integer.   The Y tile coordinate (row).
                            Uses the Google Maps Tile Coordinates.
                            - https://developers.google.com/maps/documentation/javascript/coordinates
        ---------------     --------------------------------------------------------------------
        out_format          Required string. The format of the tile output.
                            The available values are:
                                -jpg - always JPEG
                                -png - always PNG
                                -img - JPEG by default, PNG when the tile is partial
                            Note that imagery is stored on Nearmap's servers as JPEG, so switching to PNG
                            does not result in improvement in quality, however it will increase the size of
                            the response.
        ---------------     --------------------------------------------------------------------
        out_image           Required string.  The output fil path or string "bytes" for streaming
        ===============     ====================================================================

        :return: out_image or bytes

        """
        return _api.tileSurveyV3(self.base_url, self.api_key, surveyid, contentType, z, x, y, out_format, out_image)
