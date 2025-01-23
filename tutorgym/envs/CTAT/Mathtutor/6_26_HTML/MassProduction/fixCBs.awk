BEGIN {
    inEdge=0; inMsg=0
}
$0~/^ *<[\/]edge> *$/ {
    inEdge=0
}
$0~/^ *<edge> *$/ {
    inEdge=1; s=""; cbId=""
}
inEdge && $0~/^ *<[\/]message> *$/ {
    inMsg=0
}
inEdge && $0~/^ *<message> *$/ {
    inMsg=1; newInput=""
}
inEdge && $0~/^ *<[\/]matcher> *$/ {
    inMatcher=0;
    printf("%5d: inMatcher=0 %s;\n", NR, $0) >> "/dev/stderr"
}
inEdge && ( $0~/^ *<matcher> *$/ || $0~/^ *<matchers .*> *$/ ){
    inMatcher=1; newMatch="";
    printf("%5d: inMatcher=1 %s;\n", NR, $0) >> "/dev/stderr"
}
inEdge && $0~/^ *<[\/]matchers> *$/ {
    inMatchers=0;
    printf("%5d: inMatchers=0 %s;\n", NR, $0) >> "/dev/stderr"
}
inEdge && $0~/^ *<matchers [^>]*> *$/ {
    inMatchers=1; newMatch="";
    printf("%5d: inMatchers=1 %s;\n", NR, $0) >> "/dev/stderr"
}
inEdge && inMsg && $0~/^ *<Selection> *$/ {
    print;
    if(getline && (s=gensub(/^ *<value>([^<]*)([^<]*)<[\/]value> *$/,"\\1", 1, $0)) && match(s,/^w[12]cb[^<]+$/))
	cbId=s;
    printf("%5d: %s; s %s; cbId %s;\n", NR, $0, s, cbId) >> "/dev/stderr"
}
inEdge && inMsg && $0~/^ *<Input> *$/ {
    print;
    if(getline && cbId && match($0,/^ *<value>undefined.*<[\/]value> *$/)) {
	newInput=gensub(/^( *<value>)undefined([^<]*)(<[\/]value> *)$/,sprintf("\\1%s_check\\2\\3", cbId), 1, $0);
	printf("%5d: %s;\n", NR, newInput) >> "/dev/stderr";
	print newInput; next
    }
}
inEdge && inMatcher && $0~/^ *<matcherParameter +name="selection">.*$/ {
    if((t=gensub(/^ *<matcherParameter [^>]*>([^<]*)([^<]*)<[\/]matcherParameter> *$/,"\\1", 1, $0)) && match(t,/^w[12]cb[^<]+$/))
	cbId=t;
    printf("%5d: %s; t %s; cbId %s;\n", NR, $0, t, cbId) >> "/dev/stderr"
}
inEdge && inMatcher && $0~/^ *<matcherParameter +name="input">.*$/ {
    if(cbId && match($0,/^ *<matcherParameter [^>]*>undefined.*<[\/]matcherParameter> *$/)) {
	newMatch=gensub(/^( *<matcherParameter [^>]*>)undefined([^<]*)(<[\/]matcherParameter> *)$/,sprintf("\\1%s_check\\2\\3", cbId), 1, $0);
	printf("%5d: %s;\n", NR, newMatch) >> "/dev/stderr";
	print newMatch; next
    }
}
inEdge && inMatchers && $0~/^ *<Selection> *$/ {
    print;
    while(getline) {
	print;
	if($1=="<matcherParameter") break
    }
    if((t=gensub(/^ *<matcherParameter [^>]*>([^<]*)([^<]*)<[\/]matcherParameter> *$/,"\\1", 1, $0)) && match(t,/^w[12]cb[^<]+$/))
	cbId=t;
    printf("%5d: %s; t %s; cbId %s;\n", NR, $0, t, cbId) >> "/dev/stderr";
    next
}
inEdge && inMatchers && $0~/^ *<Input> *$/ {
    print;
    while(getline) {
	if($1=="<matcherParameter") break;
	print
    }
    if(cbId && match($0,/^ *<matcherParameter [^>]*>undefined.*<[\/]matcherParameter> *$/)) {
	newMatch=gensub(/^( *<matcherParameter [^>]*>)undefined([^<]*)(<[\/]matcherParameter> *)$/,sprintf("\\1%s_check\\2\\3", cbId), 1, $0);
	printf("%5d: %s;\n", NR, newMatch) >> "/dev/stderr";
	print newMatch; next
    }
}
 {
    print
}
