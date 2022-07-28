/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

typedef list<i32>( cpp.template = "std::list" ) int_linked_list

struct foo {
    1: required i32 bar ( presence = "required" ),
    2: required i32 baz ( presence = "manual", cpp.use_pointer = "" ),
    3: required i32 qux,
    4: required i32 bop,
} ( cpp.type = "DenseFoo", python.type = "DenseFoo", java.final = "", annotation.without.value )

const string default_user = "\'default_user\'" ;
const string default_name = '"abc\'s"' ;

exception foo_error {
    1: required i32 error_code ( foo = "bar\'" ),
    2: required string error_msg,
} ( foo = "bar" )

typedef string ( unicode.encoding = "UTF-16" ) non_latin_string ( foo = "bar" )
typedef list<double ( cpp.fixed_point = "16" )> tiny_float_list

enum weekdays {
    SUNDAY ( weekend = "yes" ),
    MONDAY,
    TUESDAY,
    WEDNESDAY,
    THURSDAY,
    FRIDAY,
    SATURDAY ( weekend = "yes" ),
} ( foo.bar = "baz" )

/* Note that annotations on senum values are not supported. */

struct ostr_default {
    1: required i32 bar,
}

struct ostr_custom {
    1: required i32 bar,
} ( cpp.customostream )

service foo_service {
    void foo() ( foo = "bar" ),
} ( a.b = "c" )

service deprecate_everything {
    # TODO: fix LITERAL
    void Foo() ( deprecated = "This method has neither 'x' nor \"y\"" ),
    void Bar() ( deprecated = "Fails to deliver ä¸­æ–‡ ÐºÐ¾Ð»Ð±Ð°ÑÐ°" ),
    void Baz() ( deprecated = "Need this to work with tabs (\t) or Umlauts (Ã¤Ã¶Ã¼Ã„Ã–ÃœÃŸ) too" ),
    void Deprecated() ( deprecated ),                                                               // no comment
}