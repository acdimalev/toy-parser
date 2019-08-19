class ParseResult:
    pass


class ParseOk(ParseResult):
    def __init__(self, matched, remaining):
        self.matched = matched
        self.remaining = remaining
    def __repr__(self):
        return "ParseOk({!r}, {!r})".format(self.matched, self.remaining)
    def __iter__(self):
        return iter([self.matched, self.remaining])


class ParseError(ParseResult):
    def __init__(self, reason):
        self.reason = reason
    def __repr__(self):
        return "ParseError({!r})".format(self.reason)
    def __iter__(self):
        return iter([self.reason])


class Parser:
    pass


class Literal(Parser):
    def __init__(self, literal):
        self.literal = literal
    def __str__(self):
        return repr(self.literal)
    def parse(self, document):
        (head, tail) = (document[:1], document[1:])
        if self.literal == head:
            return ParseOk(head, tail)
        else:
            return ParseError("Expected {} found {!r}".format(self, head))


class Range(Parser):
    def __init__(self, first, last):
        self.first = first
        self.last = last
    def __str__(self):
        return "{!r}-{!r}".format(self.first, self.last)
    def parse(self, document):
        (head, tail) = (document[:1], document[1:])
        if self.first <= head <= self.last:
            return ParseOk(head, tail)
        else:
            return ParseError("Expected {} found {!r}".format(self, head))


class OneOf(Parser):
    def __init__(self, children):
        self.children = list(children)
    def __str__(self):
        return "( {} )".format(" | ".join(map(str, self.children)))
    def parse(self, document):
        for child in self.children:
            result = child.parse(document)
            if ParseOk == type(result):
                return result
        head = document[:1]
        return ParseError("Expected {} found {!r}".format(self, head))


class Many(Parser):
    def __init__(self, child):
        self.child = child
    def __str__(self):
        return "{{ {} }}".format(self.child)
    def parse(self, document):
        matched = []
        remaining = document
        while True:
            result = self.child.parse(remaining)
            if ParseError == type(result):
                break
            matched += [result.matched]
            remaining = result.remaining
        return ParseOk(matched, remaining)


class Sequence(Parser):
    def __init__(self, children):
        self.children = list(children)
    def __str__(self):
        return "( {} )".format(", ".join(map(str, self.children)))
    def parse(self, document):
        matched = []
        remaining = document
        for child in self.children:
            result = child.parse(remaining)
            if ParseError == type(result):
                return result
            matched += [result.matched]
            remaining = result.remaining
        return ParseOk(matched, remaining)


class Optional(Parser):
    def __init__(self, child):
        self.child = child
    def __str__(self):
        return "[ {} ]".format(self.child)
    def parse(self, document):
        result = self.child.parse(document)
        if ParseOk == type(result):
            return ParseOk([result.matched], result.remaining)
        return ParseOk([], document)


class Map(Parser):
    def __init__(self, child, function):
        self.child = child
        self.function = function
    def __str__(self):
        return str(self.child)
    def parse(self, document):
        result = self.child.parse(document)
        if ParseOk == type(result):
            return ParseOk(self.function(result.matched), result.remaining)
        return result


class GrammerParser(Parser):
    def __init__(self, grammer, term):
        self.grammer = grammer
        self.term = term
    def __str__(self):
        return self.term
    def parse(self, document):
        return self.grammer._parsers[self.term].parse(document)


class Grammer:
    def __init__(self, terms):
        self._terms = {term: GrammerParser(self, term) for term in terms}
        self._parsers = {term: None for term in terms}
    def __getattr__(self, name):
        if name in self._terms:
            return self._terms[name]
        else:
            raise AttributeError
    def __dir__(self):
        return object.__dir__(self) + list(self._terms)
    def __str__(self):
        return "\n".join(
            "{}: {} ;".format(term, parser)
            for (term, parser) in self._parsers.items()
        )


def define_grammer(grammer, definition):
    for (term, parser) in definition.items():
        grammer._parsers[term] = parser
