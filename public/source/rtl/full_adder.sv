module full_adder(input a,b,cin,output sum,cout);
 wire p=a^b; assign sum=p^cin; assign cout=(a&b)|(p&cin);
endmodule
