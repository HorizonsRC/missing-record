SELECT Sites.SiteID, SiteName, Regions.RegionName
  FROM Sites
  INNER JOIN RegionSites on Sites.SiteID = RegionSites.SiteID
  INNER JOIN Regions on RegionSites.RegionID = Regions.RegionID
  WHERE
    (
      Regions.RegionName = 'CENTRAL'
      OR Regions.RegionName = 'EASTERN'
      OR Regions.RegionName = 'NORTHERN'
      OR Regions.RegionName = 'LAKES AND WQ'
    )
    AND
    (
      RecordingAuthority1 = 'MWRC'
      OR RecordingAuthority2 = 'MWRC'
    )
    AND Inactive = 0
