l = [1,3,5,7,9,11,13,15,17,19,21,23,25,29]
n=len(l)
for i in range(n):
    for j in range(i+1,n):
        for k in range(j+1,n):
            s=l[i]+l[j]+l[k]
            if s == 30:
                print(l[i],l[j],l[k])
                break
            print(l[i],l[j],l[k],s)