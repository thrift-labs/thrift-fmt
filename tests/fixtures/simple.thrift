/*x

 y*/

// hello
include "shared.thrift" // hello3

/*x

 y*/

# a
// b
include "shared2.thrift" //a

// gt

/*xyz
*/

struct Xtruct2 {
    1: required i8 byte_thing,       // used to be byte, hence the name
    2: required Xtruct struct_thing, // b
    3: required i32 i32_thing,       // a
}

struct Work {
    1: required i32 num1 = 0,
    2: required i32 num2,                       // num2 for
    // 3: required Operation op,                // op is Operation
    4: optional string comment,
    5: required map<string, list<string>> tags, //hello
}

struct Person {
    1: list<string> tags,
    2: optional list<string> opt_tags,
    3: required list<string> req_tags,
    4: string name,
    5: optional string opt_name,
    6: required string req_name,
}
