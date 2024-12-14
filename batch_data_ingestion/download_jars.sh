#!/bin/bash

# Create lib directory if it doesn't exist
mkdir -p lib

# Download the JARs
cd lib
wget https://repo1.maven.org/maven2/com/fasterxml/woodstox/woodstox-core/6.4.0/woodstox-core-6.4.0.jar
wget https://repo1.maven.org/maven2/org/codehaus/woodstox/stax2-api/4.2.1/stax2-api-4.2.1.jar
wget https://repo1.maven.org/maven2/com/google/re2j/re2j/1.7/re2j-1.7.jar
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-common/3.3.4/hadoop-common-3.3.4.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-configuration2/2.9.0/commons-configuration2-2.9.0.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-lang3/3.12.0/commons-lang3-3.12.0.jar
wget https://repo1.maven.org/maven2/org/apache/commons/commons-text/1.10.0/commons-text-1.10.0.jar
wget https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.30/mysql-connector-java-8.0.30.jar
wget https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar

cd ..
