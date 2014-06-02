<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <ns uri="http://www.tei-c.org/ns/1.0" prefix=""/>
  <pattern>
    <rule context="bibl">
      <!--<assert test="count( @[namespace-uri()='http://www.w3.org/XML/1998/namespace' and local-name()='id'] ) = 1">A bibl element has one 'id' attribute.</assert>-->
      <assert test="count( /listBibl/bibl/bibl/@*[namespace-uri()='http://www.w3.org/XML/1998/namespace' and local-name()='id'] ) = 1">A bibl element has one 'id' attribute.</assert>
    </rule>
  </pattern>
</schema>
