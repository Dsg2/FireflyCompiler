# FireflyCompiler
Modular based C transpiler + compiler caller using a minimalistic language

**Must have MSYS2 MINGW64 installed**

Project was created in hopes of simplifying C by adding a translation layer that transpiles to C. However, it is still quite basic at the current state of development, and is only suitable for basic projects.

The language is built off a system where every line starts with a keyword, simplifying transpiling and potentially making the code easier to read.

Built in keywords:
 - include: include <name> (includes a header or library)
 - var: var <name> <type> (initialises a variable of a type)
 - set: set <name> <expr> (sets a variable to something)
 - func: func <name> <type> <args> (initialises a function with arguments, for example main())
 - return: return <expr> (returns an expression)
 - call: call <name> (calls a function)
 - if: if <cond>
 - else: else
 - while: while <cond>
 - for: for <cond> (for loop, spacing matters, and must follow this format: for i = 0 i < 10 i++)
 - end: end brackets

The language takes in .json files as extensions, like how libraries work. A watered down stdio.h library (printf + scanf) is included as an example, where it simplifies that language by automatically keeping track of variable types and removes the need for format specifiers.

Overall, it acts like a line by line transpiler but with deeper functionality if extensions are used.
