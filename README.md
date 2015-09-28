Munki-Catalog-Admin
--------------

Munki-Catalog-Admin enables the manipulation of Munki packages via the web. Specifically:

# Packages: manage your production workflow by adding packages to a specific catalog in bulk.
# Manifests: create/delete manifests, and manage the contents of manfifests.
# Catalogs: view the contents of catalogs.

Munki-Catalog-Admin is an altered version of MunkiWebAdmin (v1) from Greg Neagle.
See https://github.com/munki/munkiwebadmin

This version was forked from Steve Kueng's fork of MunkiWebAdmin.

The function to manipulate pkginfo files utilises munkitools (specifically, the 
`makecatalogs` command). This has been tested on an Ubuntu 14.04 VM, but you will 
need to ensure that your nginx user has write permissions to your munki repo. Use of group 
permissions is recommended. 

Some of the original functionality of MunkiWebAdmin has been removed from Munki-Catalog-Admin,
such as reporting tools. For reporting tools, I recommend: 

* *Sal:* https://github.com/salopensource/sal
* *MunkiReport-PHP:* https://github.com/munkireport/munkireport-php

To Do
----

Munki-Catalog-Admin is still a work in progress, so shouldn't be used in production. 
*Note that package deletion is not yet functional.*
and there are security aspects to consider. 

Much documentation to do.
