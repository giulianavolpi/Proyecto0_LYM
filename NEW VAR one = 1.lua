NEW VAR one = 1
NEW MACRO goend(){
    if not (blocked?(front))
    then { move(one); goend(); }
    else { nop; }
    fi;
}


code_example = """
NEW VAR one=1;
NEW MACRO goend ()
{
if not (isBlocked?(front))
then { walk(one); goend(); }
else { nop; }
fi;
}
"""